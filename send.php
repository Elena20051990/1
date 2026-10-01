<?php
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false]);
    exit;
}

$to = 'ocenka@alkoskup.ru';

$clean = function ($s) { return str_replace(["\r", "\n"], ' ', trim((string)$s)); };
$name = $clean(isset($_POST['name']) ? $_POST['name'] : '');
$phone = $clean(isset($_POST['phone']) ? $_POST['phone'] : '');
$source = $clean(isset($_POST['source']) ? $_POST['source'] : 'Заявка с сайта');

if ($name === '' || $phone === '') {
    http_response_code(400);
    echo json_encode(['ok' => false]);
    exit;
}

$subject = '=?UTF-8?B?' . base64_encode('Заявка с alkoskup.ru: ' . $source) . '?=';
$body = "Источник: $source\r\nИмя: $name\r\nТелефон: $phone\r\n";

$attachments = [];
if (!empty($_FILES['photos']) && is_array($_FILES['photos']['name'])) {
    foreach ($_FILES['photos']['name'] as $i => $fname) {
        if ($_FILES['photos']['error'][$i] === UPLOAD_ERR_OK && $_FILES['photos']['size'][$i] > 0 && $_FILES['photos']['size'][$i] < 8 * 1024 * 1024) {
            $attachments[] = [
                'name' => basename($fname),
                'type' => $_FILES['photos']['type'][$i] ?: 'application/octet-stream',
                'data' => file_get_contents($_FILES['photos']['tmp_name'][$i]),
            ];
        }
    }
}

$headers = "From: alkoskup.ru <noreply@alkoskup.ru>\r\nReply-To: $to\r\n";

if ($attachments) {
    $boundary = md5(uniqid('', true));
    $headers .= "MIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary=\"$boundary\"\r\n";
    $message = "--$boundary\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n$body\r\n";
    foreach ($attachments as $a) {
        $message .= "--$boundary\r\n";
        $message .= "Content-Type: {$a['type']}; name=\"{$a['name']}\"\r\n";
        $message .= "Content-Transfer-Encoding: base64\r\n";
        $message .= "Content-Disposition: attachment; filename=\"{$a['name']}\"\r\n\r\n";
        $message .= chunk_split(base64_encode($a['data'])) . "\r\n";
    }
    $message .= "--$boundary--";
} else {
    $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
    $message = $body;
}

$ok = @mail($to, $subject, $message, $headers);
echo json_encode(['ok' => $ok]);
