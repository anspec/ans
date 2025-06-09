#Разработай систему управления учетными записями пользователей для н
#ебольшой компании. Компания разделяет сотрудников на обычных работников
#и администраторов. У каждого сотрудника есть уникальный идентификатор (ID),
#имя и уровень доступа. Администраторы, помимо обычных данных пользователей, имеют
#дополнительный уровень доступа и могут добавлять или удалять пользователя из системы

class User():
  def __init__(self,user_id:int,user_name:str):
    self._user_id = user_id
    self._user_name = user_name
    self._user_dost = "user"

  def get_id(self):
    return self._user_id

  def get_info(self):
    print(f"id:{self._user_id} name:{self._user_name} доступ:{self._user_dost}")

  def _set_dost(self, dost):
     self._user_dost = dost

class Admin(User):
  def __init__(self, user_name: str):
    super().__init__(1,user_name)
    self._next_user_id = 2
    self._user_dost = "admin"
    self.userList = []

  def add_user(self, user_name:str, dost:str=None):
    success = True
    for user in self.userList:
      if user._user_name == user_name:
        print(f"Пользователь с именем {user_name} уже есть! Задайте другое!")
        success = False
        break

    if success:
      new_user = User(self._next_user_id, user_name)
      self._next_user_id += 1
      if dost != None:
        new_user._set_dost(dost)
      self.userList.append(new_user)

  def remove_user(self,user_name):
    for user in self.userList:
      if user._user_name == user_name:
        print(f"Пользователь с именем {user_name} удален из списка пользователей!")
        self.userList.remove(user)
        break
  def change_dost(self, user_name:str, dost:str):
   success = False
   for user in self.userList:
     if user._user_name == user_name:
       user._set_dost(dost)
       success = True
       break

   if not success:
     print(f"Пользователь с именем {user_name} не найден!")

  def users_info(self):
    for user in self.userList:
      user.get_info()

admin = Admin("Вася")
admin.add_user("Коля")
admin.add_user("Люда")
admin.add_user("Петя")
admin.add_user("Аня")

admin.users_info()

admin.remove_user("Коля")
admin.change_dost("Петя","стажер")

admin.users_info()

