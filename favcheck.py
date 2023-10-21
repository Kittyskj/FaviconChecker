import requests
import hashlib
import telebot
import re
import time

user_last_message_time = {}

bot = telebot.TeleBot("YOUR_TELEGRAM_BOT_API_KEY")
author_name = "YOUR_NAME"


@bot.message_handler(commands=['start'])
def welcome(message):
    icon = '😁'
    welcome_msg = f'Hi, {message.from_user.first_name}! {icon}\n' \
                  f'I am bot, created {author_name} to help get sites favicon hash.\n' \
                  f'Send to this bot domain u want to be cheked. Example: google.com, do not sent url.\n'
    bot.send_message(message.from_user.id, welcome_msg)


@bot.message_handler(content_types=['text'])
def process_domain(message):
    domain = message.text.strip()
    if is_valid_domain(domain):
        if can_send_message(message.from_user.id):
            result = get_hash_favicon(domain)
            if result:
                send_html_report(result, message.from_user.id)
            else:
                bot.send_message(message.from_user.id,
                                 f"On domain {domain} didn't find favicon.ico or we cannot process this domain.")
        else:
            bot.send_message(message.from_user.id, "Please wait for 30 sec before sending another request.")
    else:
        bot.send_message(message.from_user.id, "Invalid domain. Please enter a valid domain name.")


def is_valid_domain(domain):
    pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, domain)


def can_send_message(user_id):
    last_message_time = user_last_message_time.get(user_id, 0)
    current_time = time.time()
    if current_time - last_message_time >= 30:
        user_last_message_time[user_id] = current_time
        return True
    return False


def get_hash_favicon(domain):
    domain_https = f'https://{domain}/favicon.ico'
    domain_http = f'http://{domain}/favicon.ico'
    try:
        favicon_resp = requests.get(domain_https, timeout=5)
        if favicon_resp.status_code == 200:
            md5 = hashlib.md5(favicon_resp.content).hexdigest()
            return f"{domain}: MD5 Hash - {md5}"
        else:
            favicon_resp = requests.get(domain_http, timeout=5)
            if favicon_resp.status_code == 200:
                md5 = hashlib.md5(favicon_resp.content).hexdigest()
                return f"{domain}: MD5 Hash - {md5}"
            return None
    except requests.RequestException:
        return None


def send_html_report(result, user_id):
    html_report = f"""
    <html>
    <head>
        <title>Favicon MD5 Hash Report</title>
        <style>
            body {{ background-color: #212a33; color: #ffffff; font-family: Arial, sans-serif; }}
            h1 {{ color: #ffffff; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <h1>Favicon MD5 Hash Report</h1>
        <ul>
            <li>{result}</li>
        </ul>
    </body>
    </html>
    """

    with open(f'report_{user_id}.html', 'w', encoding='utf-8') as report_file:
        report_file.write(html_report)

    bot.send_document(user_id, open(f'report_{user_id}.html', 'rb'))
    bot.send_message(user_id, "Your HTML report has been generated.")


bot.polling(none_stop=True)
