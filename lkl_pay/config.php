<?php
return [
    'python_api' => [
        'title' => 'Python后端地址',
        'type'  => 'text',
        'value' => '',
        'tip'   => '以http://或https://开头，不以/结尾',
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