import os
from typing import List
from bs4 import BeautifulSoup
import requests


headers = {
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}


def take_poets_by_location():
    page = 1
    full_list = []
    while True:
        URL = f'https://www.rekhta.org/PoetCollection?info=locationwiseentity&lang=1&StartsWith=All&route=%27location/pakistan/&pageNumber={page}'
        req = requests.get(URL, headers=headers)
        src = req.text

        soup = BeautifulSoup(src, 'lxml')

        all_poets = soup.select('.poetNameDatePlace a')
        all_hrefs = [href.get('href') for href in all_poets]

        if not all_poets:
            break
        print(len(all_hrefs), all_hrefs)

        full_list.extend(all_hrefs)
        page += 1

    with open('data/all_poets.txt', 'w') as file:
        file.writelines(f"{item}\n" for item in full_list)
    print(len(full_list), full_list)


def write_to_file(path: str, string: str, *args: str | List[str]) -> None:
    """
    Save data to file with the ability to write after.\n
    path — path to file, and file-name,\n
    string — string to save,\n
    location — list of locations.
    """
    with open(path, 'a') as f:
        if args:
            data = []
            for arg in args:
                if isinstance(arg, list):
                    data.extend(arg)
                else:
                    data.append(arg)
            data = ', '.join(data)
            f.write(f"{data} - {string}\n")
        else:
            f.write(f"{string}\n")


def take_nazms_url():
    with open('data/all_poets.txt') as file:
        src = file.readlines()

    for poet_url in src:
        poet_url = poet_url.strip()

        if 'poet' not in poet_url:
            write_to_file('data/not_poets.txt', poet_url)
            print('__ NOT POET', poet_url)
            continue

        try:
            req = requests.get(url=poet_url, headers=headers)
            poet_html = req.text

            soup = BeautifulSoup(poet_html, 'lxml')
            location = soup.select('.poetPlace a')
            location = [item.string for item in location]

            if not location:
                write_to_file('data/no_location.txt', poet_url, 'No location')
                print('__ POET HAS NOT LOCATION')
                continue
            if 'Pakistan' not in location:
                write_to_file('data/invalid_location.txt', poet_url, location)
                print('__ ANOTHER LOCATION', location)
                continue

            works = soup.select('.searchCategory li')
            for item in works:
                work_tag = item.find('a')
                work_name = work_tag.find(string=True, recursive=False)
                if work_name == 'Nazm':
                    nazm_url = work_tag.get('href')
                    write_to_file('data/validated_poets.txt', nazm_url)
                    print(nazm_url)
                    break

        except Exception as e:
            print(f'Ошибка при обработке {poet_url}: {e}')


def take_nazms():
    with open('data/validated_poets.txt') as file:
        src = file.readlines()

    for url in src:
        url = url.strip()
        req = requests.get(url=url, headers=headers)
        nazms_html = req.text

        soup = BeautifulSoup(nazms_html, 'lxml')
        poet_name = soup.find(class_='PtNmSs').text.strip()
        poet_name = poet_name.replace(' ', '_')
        data_id = soup.find(class_='t20SrsSocial').get('data-id')

        # create nazms_hrefs list (poems list)
        page_number = 1
        nazms_hrefs = []
        while True:
            poet_collection = 'https://www.rekhta.org/PoetCollection'
            payload = {
                'lang': '1', 'SEO_Slug': 'nazms',
                'pageNumber': page_number, 'Id': data_id,
                'contentType': 'nazms', 'info': 'ghazals',
                'sort': 'popularity-desc'
            }
            request = requests.get(poet_collection, headers=headers, params=payload)
            soup2 = BeautifulSoup(request.text, 'lxml')
            group = soup2.find_all(class_='nwPoetListBody')

            if not group:
                break
            print(f'Группа {page_number}', len(group))

            page_number += 1
            counter = 1
            for div in group:
                href = div.find('a', class_=False, href=True, recursive=False).get('href')
                nazm_name = div.text.strip().replace('\n', '(').replace(' ', '_') + ')'

                nazms_hrefs.append((href, nazm_name))
                print(f'Добавлен {counter}:', nazm_name, href)
                counter += 1
        print(poet_name, len(nazms_hrefs), 'nazms')

        # save nazms(poems)
        nazm_number = 1
        for nazm_url in nazms_hrefs:
            try:
                request = requests.get(url=nazm_url[0], headers=headers)

                b = BeautifulSoup(request.text, 'lxml')
                nazm = b.find_all(class_='pMC', attrs={'data-roman': 'off'})[-1]
                lines = nazm.find_all('p')

                nazm_for_write = []
                data_p = 1
                for p in lines:
                    par = int(p.find_parent(class_='w').get('data-p'))
                    if par == data_p:
                        nazm_for_write.append(p.text.strip())
                    elif par == data_p + 1:
                        nazm_for_write.append('')
                        nazm_for_write.append(p.text.strip())
                        data_p += 1
                    else:
                        print('Ошибка в DOM-дереве документа')

                if not os.path.exists(f'data/poets/{poet_name}'):
                    os.makedirs(f'data/poets/{poet_name}')

                with open(f'data/poets/{poet_name}/{nazm_url[1]}.txt', 'w') as poet_file:
                    poet_file.writelines(f"{el}\n" for el in nazm_for_write)

                print(f'{nazm_number} nazm saved')
                nazm_number += 1
            except Exception as e:
                print(f'Ошибка в {poet_name} {nazm_number}:', e)

        print(f'{poet_name}:', 'All nazms were saved')
    print('Congratulation! All poets saved')


def main():
    take_poets_by_location()
    take_nazms_url()
    take_nazms()


if __name__ == '__main__':
    main()
