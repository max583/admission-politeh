import requests
import json
import time

CHECK_ABITURIENT = '170-307-112 17'

class Abiturient:
    def __init__(self, snils, ege):
        self.directions = {}
        self.passedDirection = 0
        self.ege = ege
        self.snils = snils

    def addDirection(self, direction, priority):
        self.directions[priority] = direction

    def passDirection(self, direction):
        self.passedDirection = direction

    def removed(self,):
        self.removed = True

class Direction:
    def __init__(self, code, name):
        self.counter = 0
        self.passEge = 300
        self.students = []
        self.limit = 0
        self.code = code
        self.name = name
        self.laststudent = ''

    def isAvailable(self):
        return self.limit > self.counter

    def addAbiturient(self, ege, snils):
        self.counter += 1
        self.passEge = ege
        self.students.append(snils)
        self.laststudent = snils

print("Загружаем направления.")
page = 1
totalPages = 1
directionList = {}

while page <= totalPages:
    print('Читаем страницу',page)
    result = requests.get(f'https://enroll.spbstu.ru/applications-manager/api/v1/directions/all-pageable?name=&educationFormId=2&educationLevelId=2%2C5&admissionBasis=BUDGET&showClosed=true&page={page}',
                          headers={'Accept':'*/*','Accept-Encoding':'gzip, deflate, br','Connection':'keep-alive',
                                   'User-Agent':'PostmanRuntime/7.32.3'})
    if 200 != result.status_code:
        RuntimeError(f'Ошибка чтения направлений. Status code = {result.status_code}, page = {page}, \nResponce: \n{result.text}')

    json_result = json.loads(result.text)
    totalPages = json_result['totalPages']

    for direction in json_result['result']:
        id = direction['id']
        if not id in directionList:
            directionList[id] = Direction(direction['code'], direction['title'])
            if 'educationProgram' in direction:
                directionList[id].name = directionList[id].name + ' ' + direction['educationProgram']['title']
            print(id, directionList[id].code,directionList[id].name)
        else:
            RuntimeError(f'Направление id {id} обнаружено второй раз на странице {page}')

    time.sleep(1)
    page += 1

print('Всего направлений:',len(directionList))

print("Загружаем абитуриентов.")

abiturientList = {}

for id, direction in directionList.items():
    print(f'Направление id {id} {direction.name}')
    result = requests.get(
        f'https://enroll.spbstu.ru/applications-manager/api/v1/admission-list/form-rating?applicationEducationLevel=BACHELOR&directionEducationFormId=2&directionId={id}',
        headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Connection': 'keep-alive',
                 'User-Agent': 'PostmanRuntime/7.32.3'})

    if 200 != result.status_code:
        RuntimeError(f'Ошибка чтения абитуриентов направления {id}. Status code = {result.status_code}, \nResponce: \n{result.text}')

    json_result = json.loads(result.text)
    direction.limit = json_result['directionCapacity']

    abiturientSum = 0

    for abiturient in json_result['list']:
        if abiturient['withoutExam']:
            ege = 310
        else:
            ege = abiturient['fullScore']

        snils = abiturient['userSnils']

        if not snils in abiturientList:
            abiturientList[snils] = Abiturient(snils, ege)

        abiturientList[snils].addDirection(id, int(abiturient['priority']))
        abiturientSum += 1

    print(f"Загружено абитуриентов по направлению: {abiturientSum}")
    time.sleep(1)

print(f"Всего абитуриентов загружено: {len(abiturientList)}")

print("Распределяем абитуриентов")
allocatedAbiturientSnils = []

for snils, abiturient in sorted(abiturientList.items(), key=lambda x: x[1].ege,reverse=True):
    for priority in sorted(abiturient.directions):
        direction_id = abiturient.directions[priority]
        if directionList[direction_id].isAvailable():
            directionList[direction_id].addAbiturient(abiturient.ege,abiturient.snils)
            abiturient.passedDirection = direction_id
            allocatedAbiturientSnils.append(snils)
            break

print("Проходные баллы по направлениям")
for _, direction in directionList.items():
    print(f'{direction.name}, лимит: {direction.limit}, распределено: {direction.counter}, проходной балл {direction.passEge}, последний зачисленный {direction.laststudent}')

print(f'\nАбитуриент {CHECK_ABITURIENT}, направления:')
for pr in sorted(abiturientList[CHECK_ABITURIENT].directions):
    dir_id = abiturientList[CHECK_ABITURIENT].directions[pr]
    print('Приоритет', pr, ', проходной балл:', directionList[dir_id].passEge , directionList[dir_id].name)

if abiturientList[CHECK_ABITURIENT].passedDirection == 0:
    print('Баллы ЕГЭ', abiturientList[CHECK_ABITURIENT].ege, ', не проходит ни на какое направление.')
else:
    print('Баллы ЕГЭ',abiturientList[CHECK_ABITURIENT].ege, ', проходит на направление:', directionList[abiturientList[CHECK_ABITURIENT].passedDirection].name)
