import requests
from dotenv import load_dotenv
import os
from terminaltables import AsciiTable

def get_ansi_table(top_languages, title):
    TABLE_DATA =[]
    TABLE_DATA.append(['Язык программирования','Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'])
    for key, calc in top_languages.items():
        TABLE_DATA.append([key, calc["vacancies_found"], calc["vacancies_processed"], calc["average_salary"]])

    table_instance = AsciiTable(TABLE_DATA, title)
    table_instance.justify_columns[1] = 'right'
    table_instance.justify_columns[2] = 'right'
    table_instance.justify_columns[3] = 'right'
    return table_instance.table



def predict_rub_salary_hh(vacancie):
    if vacancie["salary"] is None:
        return None
    salary_from = vacancie["salary"]["from"]
    salary_to = vacancie["salary"]["to"]
    salary_currency = vacancie["salary"]["currency"]
    if salary_currency != 'RUR' or (not salary_from and not salary_to):
        return None
    if salary_from and not salary_to:
        return salary_from * 1.2
    if not salary_from and salary_to:
        return salary_to * 0.8

    return (salary_from+salary_to)/2

def predict_rub_salary_sj(vacancie):
    salary_from = vacancie["payment_from"]
    salary_to = vacancie["payment_to"]
    salary_currency = vacancie["currency"]
    if salary_currency != 'rub' or ( salary_from==0 and salary_to==0):
        return None
    if salary_from and salary_to==0:
        return salary_from * 1.2
    if salary_from==0 and salary_to:
        return salary_to * 0.8

    return (salary_from+salary_to)/2

def fill_statistic_hh():
    top_languages_hh = {}
    for lang in ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Scala']:
        top_languages_hh.update({lang: {"vacancies_found": 0,
                                        "vacancies_processed": 0,
                                        "average_salary": 0,
                                        }
                                 })


    # "id": "1.221", "name": "Программирование, Разработка"  specialization
    # "id": "1"  Москва  area
    payload = {'area': "1",
               'specialization': "1.221",
               'period': "30",
               }
    url = f"https://api.hh.ru/vacancies"

    response = requests.get(url, params=payload)
    response.raise_for_status()

    found = response.json()["found"]
    page_count = found // 20 + round(found % 20)
    if page_count > 100: page_count = 99
    # print(page_count)
    page = 1
    vacancies = response.json()['items']

    while page <= page_count:
        payload = {'area': "1",
                   'page': page,
                   'specialization': "1.221",
                   'period': "30",
                   }
        response = requests.get(url, params=payload)
        response.raise_for_status()

        page_payload = response.json()['items']
        vacancies = vacancies + page_payload
        page += 1
        # print(page)

    for vacancie in vacancies:
        for key, calc in top_languages_hh.items():
            if str(key).lower() in vacancie["name"].lower():
                calc["vacancies_found"] = calc["vacancies_found"] + 1
                avg_salary = calc["average_salary"] + 1
                one_salary = predict_rub_salary_hh(vacancie)
                if one_salary:
                    calc["vacancies_processed"] = calc["vacancies_processed"] + 1
                    calc["average_salary"] = round((calc["average_salary"] + one_salary) / 2, 2)
                addon = {key: calc}
                top_languages_hh.update(addon)
                break
    return top_languages_hh

def fill_statistic_sj():
    top_languages_sj = {}
    for lang in ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Scala']:
        top_languages_sj.update({lang: {"vacancies_found": 0,
                                        "vacancies_processed": 0,
                                        "average_salary": 0,
                                        }
                                 })
    load_dotenv()
    XApiAppId = os.environ['X-Api-App-Id']
    url = f'https://api.superjob.ru/2.0/vacancies/'
    # "id":4,"id_region":46,"id_country":1,"title":"Москва","title_eng":"Moscow"
    # {"title_rus":"Разработка, программирование","url_rus":"razrabotka-po","title":"Разработка, программирование","id_parent":33,"key":48}
    headers = {'X-Api-App-Id': XApiAppId}
    payload = {"town": 4,
               "catalogues": 48,
               }

    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()

    found = response.json()["total"]
    page_count = found // 20 + round(found % 20)
    if page_count > 25: page_count = 24
    # print(page_count)
    page = 1
    vacancies = response.json()['objects']
    while page <= page_count:
        payload = {"town": 4,
                   "catalogues": 48,
                   'page': page,
                   }
        response = requests.get(url, params=payload, headers=headers)
        response.raise_for_status()

        page_payload = response.json()['objects']
        vacancies = vacancies + page_payload
        page += 1
        # print(page)

    for vacancie in vacancies:
        for key, calc in top_languages_sj.items():
            if str(key).lower() in vacancie["profession"].lower():
                calc["vacancies_found"] = calc["vacancies_found"] + 1
                avg_salary = calc["average_salary"] + 1
                one_salary = predict_rub_salary_sj(vacancie)
                if one_salary:
                    calc["vacancies_processed"] = calc["vacancies_processed"] + 1
                    calc["average_salary"] = round((calc["average_salary"] + one_salary) / 2, 2)
                addon = {key: calc}
                top_languages_sj.update(addon)
                break
    return top_languages_sj


def main():
    top_languages_hh={}
    top_languages_hh.update(fill_statistic_hh())
    top_languages_sj = {}
    top_languages_sj.update(fill_statistic_sj())

    print(get_ansi_table(top_languages_hh, 'HH Moscow'))
    print()
    print(get_ansi_table(top_languages_sj, 'SuperJob Moscow'))
    print()


if __name__ == "__main__":
    main()