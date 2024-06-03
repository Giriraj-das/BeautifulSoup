import csv
import json
import os
import random
from time import sleep

from bs4 import BeautifulSoup
import requests

url = 'https://health-diet.ru/table_calorie/?utm_source=leftMenu&utm_medium=table_calorie'
headers = {
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}


def take_all_categories():
    request = requests.get(url, headers=headers)

    soup = BeautifulSoup(request.text, 'lxml')
    all_products_hrefs = soup.find_all(class_='mzr-tc-group-item-href')

    all_categories_dict = {}
    for item in all_products_hrefs:
        item_text = item.string
        item_href = 'https://health-diet.ru' + item.get('href')
        all_categories_dict[item_text] = item_href

    with open('all_categories_dict.json', 'w') as file:
        json.dump(all_categories_dict, file, indent=4, ensure_ascii=False)


def write_data():
    with open('all_categories_dict.json') as file:
        all_categories = json.load(file)

    iteration_count = len(all_categories) - 1
    count = 0
    print(f'Всего итераций: {iteration_count}')

    for category_name, category_href in all_categories.items():

        rep = [", ", ",", " ", "-", "'"]
        for item in rep:
            if item in category_name:
                category_name = category_name.replace(item, "_")

        req = requests.get(url=category_href, headers=headers)
        src = req.text

        soup = BeautifulSoup(src, 'lxml')

        # проверка страницы на наличие таблицы с продуктами
        alert_block = soup.find(class_='uk-alert-danger')
        if alert_block:
            continue

        # собираем заголовки таблицы
        table_head = soup.select('.mzr-tc-group-table thead tr th')
        product = table_head[0].string
        calories = table_head[1].string
        proteins = table_head[2].string
        fats = table_head[3].string
        carbohydrates = table_head[4].string

        if not os.path.exists(f'data'):
            os.makedirs(f'data')

        with open(f'data/{count}_{category_name}.csv', 'w', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow((product, calories, proteins, fats, carbohydrates))

        # собираем данные продуктов
        products_data = soup.select('.mzr-tc-group-table tbody tr')

        product_info = []
        for item in products_data:
            product_tds = item.find_all('td')

            title = product_tds[0].find('a').string
            calories = product_tds[1].string
            proteins = product_tds[2].string
            fats = product_tds[3].string
            carbohydrates = product_tds[4].string

            product_info.append(
                {
                    "Title": title,
                    "Calories": calories,
                    "Proteins": proteins,
                    "Fats": fats,
                    "Carbohydrates": carbohydrates,
                }
            )

            with open(f'data/{count}_{category_name}.csv', 'a', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow((title, calories, proteins, fats, carbohydrates))

        with open(f'data/{count}_{category_name}.json', 'a', encoding='utf-8') as file:
            json.dump(product_info, file, indent=4, ensure_ascii=False)

        count += 1
        print(f'Итерация {count}. {category_name} записан...')
        iteration_count -= 1

        if iteration_count == 0:
            print('Работа завершена')
            break

        print(f'Осталось итераций: {iteration_count}')
        sleep(random.randrange(2, 4))


def main():
    take_all_categories()
    write_data()


if __name__ == '__main__':
    main()
