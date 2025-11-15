import os
import time
import threading
import json
import logging
import uvicorn
import requests
import hashlib
import hmac
from urllib.parse import urlparse, parse_qs, unquote
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Union, Optional

app = FastAPI()

# 添加请求验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("="*80)
    logger.error("请求验证失败 - 422 Unprocessable Content")
    logger.error(f"请求URL: {request.url}")
    logger.error(f"请求方法: {request.method}")
    logger.error(f"验证错误详情: {json.dumps(exc.errors(), ensure_ascii=False, indent=2)}")
    logger.error("="*80)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

CONFIG = {}

def load_config():
    """
    读取本地配置文件 config.json
    """
    try:
        base = os.path.dirname(__file__)
        path = os.path.join(base, 'config.json')
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f) or {}
    except Exception:
        return {}

CONFIG = load_config()

logger = logging.getLogger("python_api")
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'app.log'), encoding='utf-8')
_ch = logging.StreamHandler()
_fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
_fh.setFormatter(_fmt)
_ch.setFormatter(_fmt)
if not logger.handlers:
    logger.addHandler(_fh)
    logger.addHandler(_ch)


class CreateOrderReq(BaseModel):
    invoice_id: Union[str, int]
    tradeAmount: str
    remark: str = ""
    notify_url: str
    return_url: str
    
    @field_validator('invoice_id', mode='before')
    @classmethod
    def convert_invoice_id(cls, v):
        """将 invoice_id 转换为字符串"""
        return str(v)


class QueryOrderReq(BaseModel):
    payOrderNo: str
    channelId: str = "15"


def lakala_headers():
    return {"Content-Type": "application/json"}

watches = {}

def get_currency_default():
    """
    获取默认货币单位
    """
    return CONFIG.get("CURRENCY") or os.getenv("CURRENCY", "CNY")


def generate_signature(data: dict, secret: str) -> str:
    """
    生成签名：对数据进行签名以防止篡改
    """
    # 按key排序
    sorted_items = sorted(data.items())
    # 拼接字符串
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_items]) + f"&key={secret}"
    # 计算MD5
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()


def verify_api_key(api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """
    验证API密钥
    """
    expected_key = CONFIG.get("API_SECRET_KEY") or os.getenv("API_SECRET_KEY")
    if not expected_key:
        # 如果未配置密钥，警告但允许通过（向后兼容）
        logger.warning("未配置API_SECRET_KEY，建议配置以增强安全性")
        return True
    
    if not api_key or api_key != expected_key:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    return True


# 已处理的订单号缓存（防重放攻击）
processed_orders = set()
MAX_PROCESSED_ORDERS = 10000  # 最多缓存1万个订单号


@app.post("/lakala/create_order")
def create_order(req: CreateOrderReq, api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """
    创建拉卡拉收银台订单并返回支付链接
    需要API密钥认证（如果配置了API_SECRET_KEY）
    """
    # API密钥验证
    verify_api_key(api_key)
    
    # 验证 notify_url 是否在白名单中
    allowed_domains = CONFIG.get("ALLOWED_CALLBACK_DOMAINS") or []
    if allowed_domains:
        notify_domain = urlparse(req.notify_url).netloc
        if notify_domain not in allowed_domains:
            logger.error(f"回调域名不在白名单中: {notify_domain}")
            raise HTTPException(status_code=403, detail="回调地址不被允许")
    
    # 记录收到的请求（隐藏敏感信息）
    logger.info("="*80)
    logger.info("收到创建订单请求")
    safe_req = req.dict()
    logger.info(f"请求体: invoice_id={safe_req['invoice_id']}, amount={safe_req['tradeAmount']}")
    
    merch_id = CONFIG.get("LAKALA_MERCH_ID")
    key = CONFIG.get("LAKALA_KEY")
    origin = CONFIG.get("LAKALA_ORIGIN")
    key = CONFIG.get("LAKALA_KEY")
    origin = CONFIG.get("LAKALA_ORIGIN")

    payload = {
        "merchId": merch_id,
        "orderTemplateData": [
            {
                "key": key,
                "type": "number",
                "index": 0,
                "label": "支付金额",
                "value": float(req.tradeAmount),
                "origin": origin,
                "options": {
                    "label": "支付金额",
                    "content": req.tradeAmount,
                    "required": True,
                    "labelAlign": ""
                },
                "displayName": "金额类型",
                "formItemFlag": False,
                "settingsTitle": "金额类型设置",
                "marginLeftRight": 10,
                "marginTopBottom": 5,
                "cashierTemplateName": "仙林云",
                "state": True
            }
        ],
        "tradeAmount": req.tradeAmount,
        "remark": req.remark or "",
    }
    
    # 记录发送到拉卡拉的请求
    headers = lakala_headers()
    logger.info("-"*80)
    logger.info("发送到拉卡拉的请求:")
    logger.info(f"URL: https://jfyconsole.lakala.com/order/api/cashier/pay")
    logger.info(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    logger.info(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    url = "https://jfyconsole.lakala.com/order/api/cashier/pay"
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    
    # 记录拉卡拉的响应
    logger.info("-"*80)
    logger.info("拉卡拉响应:")
    logger.info(f"状态码: {resp.status_code}")
    logger.info(f"响应头: {json.dumps(dict(resp.headers), ensure_ascii=False, indent=2)}")
    
    if resp.status_code != 200:
        logger.error(f"拉卡拉接口返回错误状态码: {resp.status_code}")
        logger.error(f"响应内容: {resp.text}")
        logger.info("="*80)
        raise HTTPException(status_code=resp.status_code, detail="拉卡拉接口错误")

    body = resp.json()
    logger.info(f"响应体: {json.dumps(body, ensure_ascii=False, indent=2)}")
    
    code_str = str(body.get("code"))
    # 拉卡拉成功的code可能是 0, 000000, 200
    if code_str not in ("0", "000000", "200") or not body.get("data"):
        logger.error(f"拉卡拉返回业务错误: code={code_str}, msg={body.get('msg')}")
        logger.error(f"完整响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
        logger.info("="*80)
        raise HTTPException(status_code=400, detail=body.get("msg") or "创建订单失败")

    data = body["data"]
    pay_url = data.get("payUrl") or data.get("payurl") or data.get("pay_url")
    if not pay_url:
        logger.error(f"missing payUrl in data={json.dumps(data, ensure_ascii=False, indent=2)}")
        logger.info("="*80)
        raise HTTPException(status_code=500, detail=f"返回体缺少payUrl: {data}")

    # 提取 payOrderNo：优先从 data 中获取，否则从 URL 中解析
    pay_order_no = data.get("payOrderNo")
    if not pay_order_no:
        try:
            # 先解码 URL，因为参数可能是编码的
            decoded_url = unquote(pay_url)
            logger.info(f"解码后的URL: {decoded_url}")
            
            # 解析查询参数
            parsed = urlparse(decoded_url)
            qs = parse_qs(parsed.query)
            pay_order_no = (qs.get("payOrderNo") or qs.get("payorderno") or qs.get("pay_order_no") or [None])[0]
            
            logger.info(f"从URL提取到的参数: {qs}")
        except Exception as e:
            logger.error(f"从URL提取payOrderNo失败: {e}", exc_info=True)
            pay_order_no = None
    
    logger.info(f"最终提取结果: payUrl={pay_url[:100]}... payOrderNo={pay_order_no}")

    # 启动后台轮询支付状态并在成功时回调PHP
    start_order_watch(
        pay_order_no=pay_order_no,
        invoice_id=req.invoice_id,
        trade_amount=req.tradeAmount,
        currency=get_currency_default(),
        notify_url=req.notify_url,
    )
    logger.debug(f"start_watch invoice_id={req.invoice_id} pay_order_no={pay_order_no}")
    logger.info("="*80)

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "payUrl": pay_url,
            "payOrderNo": pay_order_no,
            "invoice_id": req.invoice_id,
        },
    }


@app.post("/lakala/query_order")
def query_order(req: QueryOrderReq):
    """
    查询拉卡拉订单状态
    """
    payload = {
        "reqData": {
            "channelId": req.channelId,
            "payOrderNo": req.payOrderNo,
        }
    }
    url = "https://payment.lakala.com/m/los/api/mch/queryFullOrder"
    logger.info(f"查询订单请求: {json.dumps(payload, ensure_ascii=False)}")
    resp = requests.post(url, json=payload, headers=lakala_headers(), timeout=10)
    logger.info(f"查询订单响应状态: {resp.status_code}")
    if resp.status_code != 200:
        logger.error(f"查询订单失败: status={resp.status_code}")
        raise HTTPException(status_code=resp.status_code, detail="拉卡拉接口错误")
    body = resp.json()
    logger.info(f"查询订单响应体: {json.dumps(body, ensure_ascii=False)}")
    return body


def start_order_watch(pay_order_no: str, invoice_id: str, trade_amount: str, currency: str, notify_url: str):
    """
    启动订单支付状态轮询线程
    每5秒查询一次，检测到支付成功后，向PHP回调通知并结束轮询
    """
    if not pay_order_no:
        return
    if pay_order_no in watches:
        return

    stop_flag = threading.Event()
    watches[pay_order_no] = stop_flag

    t = threading.Thread(
        target=order_watch_loop,
        args=(pay_order_no, invoice_id, trade_amount, currency, notify_url, stop_flag),
        daemon=True,
        name=f"watch-{pay_order_no}",
    )
    t.start()
    logger.debug(f"watch thread started for {pay_order_no}")


def order_watch_loop(pay_order_no: str, invoice_id: str, trade_amount: str, currency: str, notify_url: str, stop_flag: threading.Event):
    """
    订单轮询主循环：每5秒查询拉卡拉订单状态，成功时回调PHP并退出
    成功条件：
    - 响应中存在 respData.payStatus 且为 SUCCESS/PAY_SUCCESS/PAID
    - 或者 respData.orderStatus 为 2/"2"/SUCCESS
    """
    max_attempts = int(CONFIG.get("WATCH_MAX_ATTEMPTS", os.getenv("WATCH_MAX_ATTEMPTS", "720")))  # 默认轮询1小时
    attempts = 0
    channel_id = str(CONFIG.get("LAKALA_CHANNEL_ID", os.getenv("LAKALA_CHANNEL_ID", "15")))
    
    logger.info(f"开始轮询订单状态: pay_order_no={pay_order_no}, invoice_id={invoice_id}, max_attempts={max_attempts}")

    while not stop_flag.is_set() and attempts < max_attempts:
        attempts += 1
        try:
            logger.info(f"[轮询 {attempts}/{max_attempts}] 查询订单: {pay_order_no}")
            body = query_order(QueryOrderReq(payOrderNo=pay_order_no, channelId=channel_id))
            logger.info(f"[轮询 {attempts}] 查询响应: {json.dumps(body, ensure_ascii=False)}")
            
            resp = body.get("respData") or {}
            pay_status = str(resp.get("payStatus") or "").upper()
            order_status = resp.get("orderStatus")

            # 根据文档：未支付时 orderStatus=0, payStatus=""；支付成功时 orderStatus=2, payStatus="S"
            is_paid = (
                order_status in (2, "2") or
                pay_status in ("S",)
            )
            logger.info(f"[轮询 {attempts}] orderStatus={order_status}, payStatus={pay_status}, is_paid={is_paid}")

            if is_paid:
                # 拉卡拉返回的金额单位是分，需要转换为元
                amount_fen = resp.get("actualPayAmount") or resp.get("amount") or 0
                try:
                    # 分转元：除以100
                    amount_yuan = float(amount_fen) / 100
                    # 保留两位小数
                    amount = f"{amount_yuan:.2f}"
                except Exception as e:
                    logger.error(f"金额转换失败: amount_fen={amount_fen}, error={e}")
                    # 降级使用原始的 trade_amount
                    amount = trade_amount
                
                logger.info(f"[轮询 {attempts}] 检测到支付成功! 金额转换: {amount_fen}分 -> {amount}元")
                post_notify(invoice_id, pay_order_no, amount, currency, notify_url)
                logger.info(f"支付成功回调完成: invoice_id={invoice_id} pay_order_no={pay_order_no} amount={amount}")
                break
        except Exception as e:
            logger.error(f"[轮询 {attempts}] 轮询出错: pay_order_no={pay_order_no} 错误={e}", exc_info=True)

        time.sleep(5)

    # 清理标记
    watches.pop(pay_order_no, None)
    logger.info(f"订单轮询结束: pay_order_no={pay_order_no}, 总尝试次数={attempts}")


def post_notify(invoice_id: str, pay_order_no: str, amount: str, currency: str, notify_url: str):
    """
    将支付成功结果POST到PHP的异步回调地址
    提交字段：invoice_id、payOrderNo、tradeAmount、currency、sign
    """
    # 防重放攻击：检查订单是否已处理
    global processed_orders
    if pay_order_no in processed_orders:
        logger.warning(f"订单已处理过，跳过回调: {pay_order_no}")
        return
    
    # 生成签名
    callback_secret = CONFIG.get("CALLBACK_SECRET") or os.getenv("CALLBACK_SECRET", "default_secret_key_change_me")
    sign_data = {
        "invoice_id": invoice_id,
        "payOrderNo": pay_order_no,
        "tradeAmount": amount,
        "currency": currency,
    }
    signature = generate_signature(sign_data, callback_secret)
    
    payload = {
        **sign_data,
        "sign": signature,
    }
    headers = {"Content-Type": "application/json"}
    logger.info(f"准备回调PHP: url={notify_url}")
    logger.info(f"回调payload: invoice_id={invoice_id}, amount={amount}, pay_order_no={pay_order_no}")
    
    try:
        resp = requests.post(notify_url, json=payload, headers=headers, timeout=10)
        logger.info(f"PHP回调响应: status={resp.status_code}")
        
        if resp.status_code == 200:
            # 标记订单为已处理
            processed_orders.add(pay_order_no)
            # 限制缓存大小
            if len(processed_orders) > MAX_PROCESSED_ORDERS:
                # 移除最早的1000个
                to_remove = list(processed_orders)[:1000]
                for order in to_remove:
                    processed_orders.remove(order)
        else:
            logger.error(f"回调PHP失败: status={resp.status_code}, body={resp.text}")
            raise HTTPException(status_code=500, detail=f"回调PHP失败: {resp.status_code}")
    except Exception as e:
        logger.error(f"回调PHP异常: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))