<?php
// Приём отзывов и обращений организаций: пересылает их на e-mail оператора. Ничего не сохраняет на сервере, кроме метки времени для ограничения частоты.
const TO = 'expert@gradus-rating.ru';
const FROM = 'noreply@gradus-rating.ru';   // ящик на домене сайта (создайте его в панели хостинга, если ещё нет)

header('Content-Type: application/json; charset=utf-8');
function out($code, $ok) { http_response_code($code); echo json_encode(['ok' => $ok]); exit; }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') out(405, false);
$raw = file_get_contents('php://input', false, null, 0, 20000);
$d = json_decode($raw, true);
if (!is_array($d)) out(400, false);

// Ограничение частоты: не чаще одного сообщения в 20 секунд с одного IP
$ip = $_SERVER['REMOTE_ADDR'] ?? '0';
$stamp = sys_get_temp_dir() . '/ar_' . md5($ip);
if (is_file($stamp) && time() - filemtime($stamp) < 20) out(429, false);

function f($d, $k, $max) {
    $v = isset($d[$k]) && is_string($d[$k]) ? trim($d[$k]) : '';
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F]/u', '', $v);
    return mb_substr($v, 0, $max);
}

$type = $_GET['type'] ?? '';
$replyTo = '';
if ($type === 'review') {
    $text = f($d, 'text', 2000);
    if ($text === '' || f($d, 'rating', 2) === '') out(400, false);
    $subject = 'Отзыв: ' . f($d, 'company', 120);
    $body = "Компания: " . f($d, 'company', 120) . "\nИмя: " . f($d, 'name', 80) . "\nОценка: " . f($d, 'rating', 2) . "\n\n" . $text . "\n";
} elseif ($type === 'claim') {
    $email = f($d, 'email', 120);
    if (!filter_var($email, FILTER_VALIDATE_EMAIL) || f($d, 'text', 3000) === '' || f($d, 'company', 120) === '') out(400, false);
    $replyTo = $email;
    $subject = 'Обращение организации: ' . f($d, 'company', 120);
    $body = "Организация: " . f($d, 'company', 120) . "\nСайт: " . f($d, 'site', 200) . "\nКонтактное лицо: " . f($d, 'contact', 120)
          . "\nE-mail: " . $email . "\nТип: " . f($d, 'kind', 80) . "\nПодтверждение: " . f($d, 'proof', 300)
          . "\nСогласие на обработку данных: " . (!empty($d['consent']) ? 'да' : 'нет') . "\n\n" . f($d, 'text', 3000) . "\n";
} else {
    out(400, false);
}

$headers = "From: " . FROM . "\r\nContent-Type: text/plain; charset=UTF-8\r\n";
if ($replyTo !== '') $headers .= "Reply-To: " . $replyTo . "\r\n";
$subject = '=?UTF-8?B?' . base64_encode(preg_replace('/[\r\n]+/', ' ', $subject)) . '?=';
if (!mail(TO, $subject, $body, $headers)) out(500, false);
@touch($stamp);
out(200, true);
