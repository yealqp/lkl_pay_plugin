<?php

namespace gateways\lkl_pay\controller;

use app\home\controller\OrderController;
use think\Controller;

class IndexController extends Controller
{
    /**
     * 异步回调入账
     * @return string
     */
    public function notifyHandle()
    {
        $raw = file_get_contents('php://input');
        $json = json_decode($raw, true);
        $this->log('notify_raw', ['raw' => $raw]);
        $this->log('notify_json', ['json' => $json]);

        $invoiceId = $json['invoice_id'] ?? ($_POST['invoice_id'] ?? null);
        $transId   = $json['payOrderNo'] ?? ($_POST['trans_id'] ?? null);
        $amount    = $json['tradeAmount'] ?? ($_POST['amount_in'] ?? null);
        $currency  = $json['currency'] ?? ($_POST['currency'] ?? 'CNY');
        $sign      = $json['sign'] ?? null;
        $payment   = 'LklPay';

        if (!$invoiceId || !$transId || !$amount) {
            $this->log('notify_missing_params', ['invoice_id' => $invoiceId, 'trans_id' => $transId, 'amount' => $amount]);
            return '缺少必要参数';
        }

        // 签名验证（防止伪造回调）
        if (!$this->verifySignature($json)) {
            $this->log('notify_invalid_signature', ['data' => $json]);
            return '签名验证失败';
        }

        // 检查订单是否已处理（防止重复入账）
        if ($this->isOrderProcessed($transId)) {
            $this->log('notify_duplicate_order', ['trans_id' => $transId]);
            return '订单已处理';
        }

        $data = array(
            'invoice_id' => $invoiceId,
            'trans_id'   => $transId,
            'currency'   => $currency,
            'payment'    => $payment,
            'amount_in'  => $amount,
            'paid_time'  => date('Y-m-d H:i:s'),
        );

        $Order = new OrderController();
        $Order->orderPayHandle($data);
        
        // 标记订单为已处理
        $this->markOrderProcessed($transId);
        
        $this->log('notify_order_processed', ['data' => $data]);

        return 'success';
    }

    /**
     * 验证回调签名
     * @param array $data
     * @return bool
     */
    private function verifySignature($data)
    {
        if (!isset($data['sign'])) {
            return false;
        }

        $receivedSign = $data['sign'];
        unset($data['sign']);

        // 从插件配置读取回调密钥
        try {
            $pluginName = 'LklPay';
            $config = db('plugin')->where('name', $pluginName)->value('config');
            if (empty($config) || $config == 'null') {
                $this->log('verify_signature_no_config', ['error' => '插件配置未找到']);
                return false;
            }
            $configData = json_decode($config, true);
            $secret = $configData['callback_secret'] ?? '';
            
            if (empty($secret)) {
                $this->log('verify_signature_no_secret', ['error' => '回调签名密钥未配置']);
                return false;
            }
        } catch (\Exception $e) {
            $this->log('verify_signature_error', ['error' => $e->getMessage()]);
            return false;
        }
        
        // 按key排序
        ksort($data);
        
        // 拼接字符串
        $signStr = '';
        foreach ($data as $key => $value) {
            $signStr .= $key . '=' . $value . '&';
        }
        $signStr .= 'key=' . $secret;
        
        // 计算MD5
        $expectedSign = strtoupper(md5($signStr));
        
        $this->log('verify_signature', [
            'received' => $receivedSign,
            'expected' => $expectedSign,
            'match' => ($receivedSign === $expectedSign)
        ]);
        
        return $receivedSign === $expectedSign;
    }

    /**
     * 检查订单是否已处理
     * @param string $transId
     * @return bool
     */
    private function isOrderProcessed($transId)
    {
        // TODO: 从数据库或缓存检查订单是否已处理
        // 这里简单示例，实际应该查询数据库
        $cacheFile = __DIR__ . '/../processed_orders.json';
        if (file_exists($cacheFile)) {
            $processed = json_decode(file_get_contents($cacheFile), true) ?: [];
            return in_array($transId, $processed);
        }
        return false;
    }

    /**
     * 标记订单为已处理
     * @param string $transId
     */
    private function markOrderProcessed($transId)
    {
        $cacheFile = __DIR__ . '/../processed_orders.json';
        $processed = [];
        if (file_exists($cacheFile)) {
            $processed = json_decode(file_get_contents($cacheFile), true) ?: [];
        }
        
        $processed[] = $transId;
        
        // 只保留最近1000个订单
        if (count($processed) > 1000) {
            $processed = array_slice($processed, -1000);
        }
        
        file_put_contents($cacheFile, json_encode($processed));
    }

    /**
     * 同步回调跳转
     * @return \think\response\Redirect|string
     */
    public function returnHandle()
    {
        $url = config('return_url');
        $this->log('return_handle', ['return_url' => $url]);
        if ($url) {
            return redirect($url);
        }
        return 'ok';
    }

    /**
     * 写入插件控制器日志
     * @param string $title
     * @param array $data
     * @return void
     */
    private function log($title, $data = [])
    {
        $path = __DIR__ . '/../lkl_pay_controller.log';
        $line = date('Y-m-d H:i:s') . ' ' . $title . ' ' . json_encode($data, JSON_UNESCAPED_UNICODE);
        file_put_contents($path, $line . PHP_EOL, FILE_APPEND);
    }
}