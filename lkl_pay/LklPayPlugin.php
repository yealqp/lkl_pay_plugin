<?php

namespace gateways\lkl_pay;

use app\admin\lib\Plugin;
use think\Db;

class LklPayPlugin extends Plugin
{
    public $info = array(
        'name'        => 'LklPay',
        'title'       => '拉卡拉收银台',
        'description' => '拉卡拉聚合收银台支付插件',
        'status'      => 1,
        'author'      => 'yealqp',
        'version'     => '1.0',
        'module'      => 'gateways',
    );

    public $hasAdmin = 0;

    /**
     * 安装插件
     * @return bool
     */
    public function install()
    {
        return true;
    }

    /**
     * 卸载插件
     * @return bool
     */
    public function uninstall()
    {
        return true;
    }

    /**
     * 发起支付并跳转至拉卡拉收银台链接
     * @param array $param 包含 product_name、out_trade_no、total_fee
     * @return array {type: 'jump', data: 'payUrl'}
     * @throws \Exception
     */
    public function LklPayHandle($param)
    {
        $config = $this->config();
        $domain = configuration('domain');

        $pythonApi = rtrim($config['python_api'], '/');
        if (!$pythonApi) {
            throw new \Exception('Python后端地址未配置');
        }

        $payload = [
            'invoice_id'   => $param['out_trade_no'],
            'tradeAmount'  => (string)$param['total_fee'],
            'remark'       => $param['product_name'] ?? '',
            'notify_url'   => $domain . '/gateway/lkl_pay/index/notifyHandle',
            'return_url'   => $domain . '/gateway/lkl_pay/index/returnHandle',
        ];

        $this->log('create_order_request', ['url' => $pythonApi . '/lakala/create_order', 'payload' => $payload]);
        $resp = $this->postJson($pythonApi . '/lakala/create_order', $payload);
        $this->log('create_order_response', $resp);

        if (!isset($resp['data']['payUrl'])) {
            throw new \Exception('拉卡拉返回异常：缺少payUrl');
        }

        return [
            'type' => 'jump',
            'data' => $resp['data']['payUrl'],
        ];
    }

    /**
     * 读取插件配置
     * @return array
     * @throws \Exception
     */
    public function config()
    {
        $name = $this->info['name'];
        $config = db('plugin')->where('name', $name)->value('config');
        if (!empty($config) && $config != 'null') {
            $config = json_decode($config, true);
            return $config;
        }
        throw new \Exception('请先在后台完善插件配置');
    }

    /**
     * 以JSON向Python后端POST请求
     * @param string $url
     * @param array $data
     * @return array
     * @throws \Exception
     */
    private function postJson($url, $data)
    {
        $ch = curl_init($url);
        
        // 从配置获取API密钥
        $config = $this->config();
        $apiKey = $config['api_secret_key'] ?? '';
        
        $headers = [
            'Content-Type: application/json',
        ];
        
        // 如果配置了API密钥，添加到请求头
        if ($apiKey) {
            $headers[] = 'X-API-Key: ' . $apiKey;
        }
        
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data, JSON_UNESCAPED_UNICODE));
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        $response = curl_exec($ch);
        if ($response === false) {
            $err = curl_error($ch);
            curl_close($ch);
            $this->log('post_json_error', ['url' => $url, 'error' => $err]);
            throw new \Exception('请求Python后端失败：' . $err);
        }
        curl_close($ch);
        $this->log('post_json_raw_response', ['url' => $url, 'raw' => $response]);
        $arr = json_decode($response, true);
        if (!is_array($arr)) {
            $this->log('post_json_decode_failed', ['url' => $url]);
            throw new \Exception('Python后端响应解析失败');
        }
        return $arr;
    }

    /**
     * 写入插件日志
     * @param string $title
     * @param array $data
     * @return void
     */
    private function log($title, $data = [])
    {
        $path = __DIR__ . '/lkl_pay.log';
        $line = date('Y-m-d H:i:s') . ' ' . $title . ' ' . json_encode($data, JSON_UNESCAPED_UNICODE);
        file_put_contents($path, $line . PHP_EOL, FILE_APPEND);
    }
}