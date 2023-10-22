import requests
import hashlib
import telebot
import re
import time

user_last_message_time = {}

bot = telebot.TeleBot("6937574350:AAEjG2-Rtg-Npt78HAAe6WZ9Cnm3ML5Ji20")
author_name = "ran_mao"


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
				bot.send_message(message.from_user.id, f"On domain {domain} didn't find favicon.ico or we cannot process this domain.")
		else:
			bot.send_message(message.from_user.id, "Please wait for 30 sec before sending another request.")
	else:
		bot.send_message(message.from_user.id, "Invalid domain. Please enter a valid domain name.")

@bot.message_handler(content_types=['document'])
def process_file_domains(message):
	file_name = message.document.file_name
	if file_name.split('.')[-1] in ['csv', 'lst', 'txt']:
		downloaded_file = bot.download_file(bot.get_file(message.document.file_id).file_path)
		results = []
		for line in downloaded_file.decode().split('\n'):
			domain = line.strip()
			if is_valid_domain(domain):
				result = get_hash_favicon(domain)
				print(result)
				if result:
					results.append(result[0])

		if can_send_message(message.from_user.id):
			if results:
				send_html_report(results, message.from_user.id)
			else:
				bot.send_message(message.from_user.id, f"On domains from file didn't find favicon.ico or we cannot process this domains.")
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
	domain_http = f'http://{domain}/favicon.ico'
	try:
		favicon_resp = requests.get(domain_http, timeout=5)
		if favicon_resp.status_code == 200:
			md5 = hashlib.md5(favicon_resp.content).hexdigest()
			return [f"{domain}: MD5 Hash - {md5}"]
		else:
			return None
	except requests.RequestException:
		return None

def send_html_report(results, user_id):
	html_report_header = """
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
			<ul>"""
	html_results_data = ''
	for result in results:
		html_results_data += f"<li>{result}</li>\n"

	html_report_footer = """		</ul>
		</body>
	</html>
	"""

	html_report = html_report_header + html_results_data + html_report_footer

	with open(f'report_{user_id}.html', 'w', encoding='utf-8') as report_file:
		report_file.write(html_report)

	bot.send_document(user_id, open(f'report_{user_id}.html', 'rb'))
	bot.send_message(user_id, "Your HTML report has been generated.")


bot.polling(none_stop=True)
