<?php
return [
    'python_api' => [
        'title' => 'Python后端地址',
        'type'  => 'text',
        'value' => '',
        'tip'   => '以http://或https://开头，不以/结尾',
    ],
    'api_secret_key' => [
        'title' => 'API密钥',
        'type'  => 'text',
        'value' => '',
        'tip'   => '与Python配置的API_SECRET_KEY保持一致，用于API认证',
    ],
    'callback_secret' => [
        'title' => '回调签名密钥',
        'type'  => 'text',
        'value' => '',
        'tip'   => '与Python配置的CALLBACK_SECRET保持一致，用于验证回调签名（非常重要！）',
    ],
    'currency' => [
        'title' => '支持货币单位',
        'type'  => 'text',
        'value' => 'CNY',
        'tip'   => '填写ISO货币代码，如CNY、USD',
    ],
    'notify_url'  => [
        'title'     => '回调地址',
        'type'      => 'text',
        'value'     => configuration('domain') . '/gateway/lkl_pay/index/notifyHandle',
        'tip'       => '仅展示用途，实际由插件内部使用',
        'attribute' => 'disabled',
    ],
];