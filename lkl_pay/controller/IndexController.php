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
        $payment   = 'LklPay';

        if (!$invoiceId || !$transId || !$amount) {
            $this->log('notify_missing_params', ['invoice_id' => $invoiceId, 'trans_id' => $transId, 'amount' => $amount]);
            return '缺少必要参数';
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
        $this->log('notify_order_processed', ['data' => $data]);

        return 'success';
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