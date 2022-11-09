import requests
from dotenv import load_dotenv
import os
from terminaltables import AsciiTable


def get_ansi_table(top_languages, title):
    top_languages_table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for programming_language, statistic_values in top_languages.items():
        top_languages_table.append([programming_language,
                                    statistic_values["vacancies_found"],
                                    statistic_values["vacancies_processed"],
                                    statistic_values["average_salary"]]
                                  )

    table_instance = AsciiTable(top_languages_table, title)
    table_instance.justify_columns[1] = 'right'
    table_instance.justify_columns[2] = 'right'
    table_instance.justify_columns[3] = 'right'
    return table_instance.table


def get_average_salary(salary_from, salary_to, salary_currency):
    if salary_currency != 'RUR' or (not salary_from and not salary_to):
        return None
    if salary_from and not salary_to:
        return salary_from * 1.2
    if not salary_from and salary_to:
        return salary_to * 0.8

    return (salary_from+salary_to)/2


def predict_rub_salary_hh(vacancie):
    if str(vacancie["salary"]): return None
    salary_from = vacancie["salary"]["from"]
    salary_to = vacancie["salary"]["to"]
    salary_currency = vacancie["salary"]["currency"]

    return get_average_salary(salary_from, salary_to, salary_currency)


def predict_rub_salary_sj(vacancie):
    salary_from = vacancie["payment_from"]
    salary_to = vacancie["payment_to"]
    salary_currency = vacancie["currency"]

    return get_average_salary(salary_from, salary_to, salary_currency)


def fill_statistic_hh(languages):

    top_languages_hh = {}
    for lang in languages:
        top_languages_hh.update({lang: {"vacancies_found": 0,
                                        "vacancies_processed": 0,
                                        "average_salary": 0,
                                        }
                                 })

    moscow_id = "1"
    industry_id = "1.221"
    amount_days = "30"

    payload = {'area': moscow_id,
               'specialization': industry_id,
               'period': amount_days,
               "text" : f"'{' or '.join(languages)}'",
               }
    url = f"https://api.hh.ru/vacancies"

    response = requests.get(url, params=payload)
    response.raise_for_status()

    response_json = response.json()
    found = response_json["found"]
    page_count = found // 20 + round(found % 20)
    if page_count > 100: page_count = 99
    page = 1
    vacancies = response_json['items']

    while page <= page_count:
        payload = {'area': moscow_id,
                   'page': page,
                   'specialization': industry_id,
                   'period': amount_days,
                   "text": f"'{' or '.join(languages)}'",
                   }
        response = requests.get(url, params=payload)
        response.raise_for_status()

        response_json = response.json()
        page_payload = response_json['items']
        vacancies = vacancies + page_payload
        page += 1

    for vacancie in vacancies:
        for programming_language, statistic_values in top_languages_hh.items():
            if str(programming_language).lower() in vacancie["name"].lower():
                statistic_values["vacancies_found"] = statistic_values["vacancies_found"] + 1
                one_salary = predict_rub_salary_hh(vacancie)
                if one_salary:
                    statistic_values["vacancies_processed"] = statistic_values["vacancies_processed"] + 1
                    statistic_values["average_salary"] = round((statistic_values["average_salary"] + one_salary) / 2, 2)
                top_languages_hh[programming_language] = statistic_values
                break
    return top_languages_hh


def fill_statistic_sj(x_api_app_id, languages):

    top_languages_sj = {}
    for lang in languages:
        top_languages_sj.update({lang: {"vacancies_found": 0,
                                        "vacancies_processed": 0,
                                        "average_salary": 0,
                                        }
                                 })

    url = f'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': x_api_app_id}

    moscow_id= 4
    industry_id = 48
    place_search = 1

    payload = {"town": moscow_id,
               "catalogues": industry_id,
               "keywords.srws": place_search,
               "keywords.skwc": 'or',
               "keywords.key": languages,
               }

    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()

    response_json = response.json()
    found = response_json["total"]
    page_count = found // 20 + round(found % 20)
    if page_count > 25: page_count = 24
    page = 1
    vacancies = response_json['objects']

    while page <= page_count:
        payload = {"town": moscow_id,
                   "catalogues": industry_id,
                   'page': page,
                   "keywords.srws": place_search,
                   "keywords.skwc": 'or',
                   "keywords.key": languages,
                   }
        response = requests.get(url, params=payload, headers=headers)
        response.raise_for_status()

        response_json = response.json()
        page_payload = response_json['objects']
        vacancies = vacancies + page_payload
        page += 1

    for vacancie in vacancies:
        for programming_language, statistic_values in top_languages_sj.items():
            if str(programming_language).lower() in vacancie["profession"].lower():
                statistic_values["vacancies_found"] = statistic_values["vacancies_found"] + 1
                one_salary = predict_rub_salary_sj(vacancie)
                if one_salary:
                    statistic_values["vacancies_processed"] = statistic_values["vacancies_processed"] + 1
                    statistic_values["average_salary"] = round((statistic_values["average_salary"] + one_salary) / 2, 2)
                top_languages_sj[programming_language] = statistic_values
                break
    return top_languages_sj


def main():
    load_dotenv()
    x_api_app_id = os.environ['SJ_X-API-APP-ID']
    languages = ['JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Scala']
    top_languages_hh = fill_statistic_hh(languages)
    top_languages_sj = fill_statistic_sj(x_api_app_id, languages)

    print(get_ansi_table(top_languages_hh, 'HH Moscow'))
    print()
    print(get_ansi_table(top_languages_sj, 'SuperJob Moscow'))
    print()


if __name__ == "__main__":
    main()