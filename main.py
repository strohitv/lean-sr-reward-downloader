import argparse
import datetime
import json
import os
import shutil
from pathlib import Path
from time import sleep

import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

import pathlib

from selenium.webdriver.support.select import Select

bot_url = 'http://localhost:8080'

profile_folder = str(pathlib.Path(__file__).parent.resolve().joinpath('profile'))

if not os.path.exists(profile_folder):
	os.makedirs(profile_folder, exist_ok=True)

firefox_profile = webdriver.FirefoxProfile(profile_folder)

firefox_options = webdriver.FirefoxOptions()
firefox_options.profile = firefox_profile


def load_rewards(url: str, auth: str):
	firefox = webdriver.Firefox(firefox_options)

	try:
		print_with_timestamp('opening firefox')
		firefox.get("https://leanny.github.io/splat3seedchecker/index.html#/seedlisting")

		check_rewards_tab: WebElement | None = None

		while not check_rewards_tab:
			sleep(1)

			try:
				check_rewards_tab = [button for button in firefox.find_elements(By.TAG_NAME, 'button') if
									 'Check Rewards (Salmon Run)' in button.text][0]
				print_with_timestamp('found check_rewards_tab')
			except Exception:
				pass

		check_rewards_tab.click()

		sleep(1)

		select_element: WebElement | None = None
		submit_button: WebElement | None = None

		while not select_element or not submit_button:
			sleep(1)

			try:
				select_element = firefox.find_element(By.TAG_NAME, 'select')
				print_with_timestamp('found select_element')
			except Exception:
				pass

			try:
				submit_button = \
					[button for button in firefox.find_elements(By.TAG_NAME, 'button') if
					 'Display Results' in button.text][
						0]
			except Exception:
				pass

		select = Select(select_element)
		all_options = select.options

		all_results = []

		for index, option in enumerate(all_options):
			print()
			select.select_by_index(index)
			sleep(1)

			all_result_rows = None

			while not all_result_rows:
				submit_button.click()
				sleep(1)

				all_result_rows = [tr for tr in firefox.find_elements(By.TAG_NAME, 'tr') if '00' in tr.text]

			selected_option = select.all_selected_options[0]

			print_with_timestamp(f"Next Date: {selected_option.text}")
			current_data = {
				'date': selected_option.text,
				'money': 0,
				'money_ticket_small': 0,
				'money_ticket_big': 0,
				'silver_scales': 0,
				'gold_scales': 0,
				'results': '[...]'
			}

			for row_index, row in enumerate(all_result_rows):
				print_with_timestamp(f"Row Index: #{row_index}, row text: `{row.text.split('\n')}`")

				if '(+ 50%)' in row.text:
					print_with_timestamp(f"Found +50% money ticket in row #{row_index}")
					current_data['money_ticket_small'] += 1
				elif '(+ 100%)' in row.text:
					print_with_timestamp(f"Found +100% money ticket in row #{row_index}")
					current_data['money_ticket_big'] += 1
				elif '5000' in row.text:
					print_with_timestamp(f"Found 5000 money in row #{row_index}")
					current_data['money'] += 5000
				elif '16000' in row.text:
					print_with_timestamp(f"Found 16000 money in row #{row_index}")
					current_data['money'] += 16000
				elif '32000' in row.text:
					print_with_timestamp(f"Found 32000 money in row #{row_index}")
					current_data['money'] += 32000
				elif (row_index == 4 or row_index == 16) and ('3 x' in row.text or '6 x' in row.text):
					# silver scales
					if '3' in row.text.split('\n')[1]:
						print_with_timestamp(f"Found 3 silver scales in row #{row_index}")
						current_data['silver_scales'] += 3
					else:
						print_with_timestamp(f"Found 6 silver scales in row #{row_index}")
						current_data['silver_scales'] += 6
				elif (row_index == 10 or row_index == 22) and ('1 x' in row.text or '2 x' in row.text):
					# gold scales
					if '1' in row.text.split('\n')[1]:
						print_with_timestamp(f"Found 1 gold scale in row #{row_index}")
						current_data['gold_scales'] += 1
					else:
						print_with_timestamp(f"Found 2 gold scales in row #{row_index}")
						current_data['gold_scales'] += 2

			print_with_timestamp(f"Final result object for date {selected_option.text} (results not added yet): \n{json.dumps(current_data, indent=4)}\n")
			current_data['results'] = str([r.get_attribute("outerHTML") for r in all_result_rows])
			all_results.append(current_data)

		content = json.dumps(all_results)

		try:
			requests.post(f'{url}/v1/sr-rewards', data=content, headers={'Authorization': f'Basic {auth}'})
			print_with_timestamp(f'sr rewards uploaded to {url}/v1/sr-rewards')
		except Exception as e:
			print_with_timestamp('sr reward upload to bot was not possible')
			print_with_timestamp(e)
			return

	except Exception as e:
		print_with_timestamp(e)
		# print_with_timestamp(sys.exception().__traceback__)
		print_with_timestamp(e.__context__)
		print_with_timestamp(e.__cause__)
		print_with_timestamp(e.__traceback__)
	finally:
		profile_path = Path(firefox.options.profile.path).parent.absolute()
		firefox.quit()

		if os.path.exists(profile_path):
			shutil.rmtree(profile_path)


def print_with_timestamp(obj):
	print(f'{datetime.datetime.now()}: {obj}')


def open_firefox():
	firefox = webdriver.Firefox(firefox_options)

	try:
		print_with_timestamp('opening firefox')
		firefox.get("https://leanny.github.io/splat3seedchecker/index.html#/seedlisting")

		while browser_is_open(firefox):
			sleep(1)

		print_with_timestamp('done')
	except Exception:
		pass


def browser_is_open(browser):
	try:
		_ = browser.window_handles
	except Exception:
		return False

	return True


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-o', '--open', help='Ignore other flags and just open firefox for manual work', default=False,
						action='store_true')
	parser.add_argument('-u', '--url', type=str, help='URL of your server')
	parser.add_argument('-a', '--auth', type=str, help='Server auth token')

	args = parser.parse_args()

	if args.open:
		open_firefox()
	else:
		bot_url = args.url
		print_with_timestamp(f'using url: {bot_url}')
		print_with_timestamp(f'using auth: {args.auth}')

		try:
			load_rewards(args.url, args.auth)
		except Exception as e:
			print_with_timestamp(e)
