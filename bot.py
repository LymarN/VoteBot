import datetime
import logging
from peewee import fn,SQL
import pytz
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from db import User,Rating,Like
API_TOKEN = '1601183976:AAFO62JAtT2Sy_1hDU-Is5bEDMzGI8srqbE'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot,storage=MemoryStorage())

user_data = {}

from aiogram.utils.callback_data import CallbackData

posts_cb: CallbackData = CallbackData('search', 'action', 'id', 'sum', 'other')

student_menu = ["Список викладачів","Рейтинг"]
teacher_menu = ["Інфо про себе","Рейтинг"]
specialities = ["121", "123", "141С", "141Е", "143"]
categories = ["МАНЕРА ВИКЛАДАННЯ", "ДОСТУПНІСТЬ МАТЕРІАЛУ", "АКТУАЛЬНІСТЬ МАТЕРІАЛУ"]

class Send(StatesGroup):
    send = State()
class Reg(StatesGroup):
    phone = State()
class RegTeacher(StatesGroup):
    name = State()
    photo = State()
    subject = State()
    info = State()
    speciality = State()
class Edrpou(StatesGroup):
    code = State()
    phone = State()

def main_keyboard(chat_id):
    user = User.get_or_none(User.chat_id == chat_id)
    if user.status == 'student':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(student_menu[0],student_menu[1])
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(teacher_menu[0],teacher_menu[1])
    return markup


@dp.message_handler(commands=['start'])
async def start_message(message):
    user = User.get_or_none(User.chat_id == message.chat.id)
    if user:
        if user.status:
            await bot.send_message(message.chat.id,"""Вітаю! Цей бот створений для анонімного оцінювання викладачів нашого коледжу, який в подальшому дозволить покращити рівень викладання.""",reply_markup=main_keyboard(message.chat.id))
        else:
            markup = types.InlineKeyboardMarkup()
            a = types.InlineKeyboardButton(
                text="Студент",
                callback_data=posts_cb.new(action="selectIdent",
                                           id='student',
                                           sum=0, other=0))
            b = types.InlineKeyboardButton(
                text="Викладач",
                callback_data=posts_cb.new(action="selectIdent",
                                           id='teacher',
                                           sum=0, other=0))
            markup.add(a,b)
            await bot.send_message(message.chat.id,"""Для початку оберіть, хто ви є: студент або викладач""",reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        a = types.InlineKeyboardButton(
            text="Студент",
            callback_data=posts_cb.new(action="selectIdent",
                                       id='student',
                                       sum=0, other=0))
        b = types.InlineKeyboardButton(
            text="Викладач",
            callback_data=posts_cb.new(action="selectIdent",
                                       id='teacher',
                                       sum=0, other=0))
        markup.add(a,b)
        await bot.send_message(message.chat.id,"""Вітаю! Цей бот створений для анонімного оцінювання викладачів нашого коледжу, який в подальшому дозволить покращити рівень викладання. Для подальшої роботи вкажіть, хто ви є: студент або викладач""",reply_markup=markup)

@dp.message_handler(content_types=['text'])
async def menu_list(message):
    if message.text == teacher_menu[0]:
        user = User.get_or_none(User.chat_id == message.chat.id)
        likes = Like.select().where(Like.teacher_chat_id == message.chat.id, Like.value=='like').count()
        dislikes = Like.select().where(Like.teacher_chat_id == message.chat.id, Like.value=='dislike').count()
        ratings = """"""
        for i in categories:
            rating = Rating.select(fn.AVG(Rating.value)).where(Rating.teacher_chat_id == message.chat.id,Rating.key == i).scalar()
            ratings += f"{i}: {rating if rating else 0} ⭐\n"
        await bot.send_photo(message.chat.id,user.photo,caption=f"""ПІБ: {user.full_name}
Предмети: {user.subject}
Спеціальність: {user.speciality}
Про себе: {user.info}

К-ть лайків: {likes}
К-ть дизлайків: {dislikes}

{ratings}""")
    if message.text == student_menu[0]:
        user = User.get_or_none(User.chat_id == message.chat.id)
        teachers = User.select().where(User.status == 'teacher',User.speciality.contains(user.speciality))
        if teachers:
            markup = types.InlineKeyboardMarkup()
            for i in teachers:
                a = types.InlineKeyboardButton(
                    text=i.full_name,
                    callback_data=posts_cb.new(action="selectTeacher",
                                               id=i.id,
                                               sum=0, other=0))

                markup.add(a)
            await bot.send_message(message.chat.id,'Оберіть потрібного викладача',reply_markup=markup)
        else:
            await bot.send_message(message.chat.id,'Немає викладачів в вашій спеціальності')

    if message.text == student_menu[1]:
        markup = types.InlineKeyboardMarkup()
        a = types.InlineKeyboardButton(
            text="Загальний",
            callback_data=posts_cb.new(action="rateByLikes",
                                       id=0,
                                       sum=0, other=0))

        b = types.InlineKeyboardButton(
            text=categories[0],
            callback_data=posts_cb.new(action="rateByRate",
                                       id=0,
                                       sum=0, other=0))

        markup.add(a,b)
        a = types.InlineKeyboardButton(
            text=categories[1],
            callback_data=posts_cb.new(action="rateByRate",
                                       id=1,
                                       sum=0, other=0))

        b = types.InlineKeyboardButton(
            text=categories[2],
            callback_data=posts_cb.new(action="rateByRate",
                                       id=2,
                                       sum=0, other=0))

        markup.add(a,b)
        await bot.send_message(message.chat.id,'Виберіть по якому показнику показати рейтинг',reply_markup=markup)



@dp.callback_query_handler(posts_cb.filter())
async def json_box(query: types.CallbackQuery, callback_data: dict):
    callback_data_action = callback_data['action']
    callback_data_id = callback_data['id']
    callback_data_sum = callback_data['sum']
    callback_data_other = callback_data['other']
    if callback_data_action == 'selectIdent':
        await bot.delete_message(message_id=query.message.message_id, chat_id=query.message.chat.id)
        if callback_data_id == 'student':
            markup = types.InlineKeyboardMarkup()
            ll = []
            for i in specialities:
                a = types.InlineKeyboardButton(
                    text=i,
                    callback_data=posts_cb.new(action="selectSpec",
                                               id=i,
                                               sum=0, other=0))
                ll.append(a)
                if len(ll) == 2:
                    markup.add(*ll)
                    ll = []
            markup.add(*ll)
            await bot.send_message(query.message.chat.id,"""Оберіть вашу спеціальність""",reply_markup=markup)

        if callback_data_id == 'teacher':
            await bot.send_message(query.message.chat.id,"""Вітаю! Для подальшої роботи заповніть, будь ласка, анкету. """)
            await bot.send_message(query.message.chat.id,"""Введіть ваше прізвище, ім'я та по-батькові одним повідомленням.""")
            await RegTeacher.name.set()


    if callback_data_action == 'selectSpec':
        await bot.delete_message(message_id=query.message.message_id, chat_id=query.message.chat.id)
        user = User.get_or_none(User.chat_id == query.message.chat.id)
        if not user:
            User(chat_id=query.message.chat.id,speciality=callback_data_id,reg_date=datetime.datetime.now(pytz.timezone('Europe/Kiev'))).save()
        else:
            pass
        await bot.send_message(query.message.chat.id,"""Тепер ви можете обрати викладача, якого хочете оцінити, або переглянути рейтинги.""",reply_markup=main_keyboard(query.message.chat.id))


    if callback_data_action == 'selectTeacher':
        markup = types.InlineKeyboardMarkup()
        teacher = User.get_or_none(User.id == callback_data_id)
        likes = Like.select().where(Like.teacher_chat_id == teacher.chat_id, Like.value=='like').count()
        dislikes = Like.select().where(Like.teacher_chat_id == teacher.chat_id, Like.value=='dislike').count()
        a = types.InlineKeyboardButton(
            text="👍",
            callback_data=posts_cb.new(action="rate",
                                       id=callback_data_id,
                                       sum="like", other=0))
        b = types.InlineKeyboardButton(
            text="👎",
            callback_data=posts_cb.new(action="rate",
                                       id=callback_data_id,
                                       sum='dislike', other=0))
        markup.add(a,b)
        await bot.send_photo(query.message.chat.id,teacher.photo,f"""ПІБ: {teacher.full_name}
Предмети: {teacher.subject}
Спеціальність: {teacher.speciality}
Про себе: {teacher.info}

К-ть лайків: {likes}
К-ть дизлайків: {dislikes}""",reply_markup=markup)


    if callback_data_action == 'rate':
        teacher = User.get_or_none(User.id == callback_data_id)
        rate = Like.get_or_none(Like.student_chat_id == query.message.chat.id,Like.teacher_chat_id == teacher.chat_id)
        if rate:
            rate.value = callback_data_sum
            rate.save()
        else:
            Like(student_chat_id=query.message.chat.id,teacher_chat_id=teacher.chat_id,value=callback_data_sum).save()
        ll = []
        markup = types.InlineKeyboardMarkup()
        for i in range(1,6):
            a = types.InlineKeyboardButton(
                text=f"{i} ⭐",
                callback_data=posts_cb.new(action="rateCategory",
                                           id=callback_data_id,
                                           sum=0, other=i))
            ll.append(a)
        markup.add(*ll)
        await bot.send_message(query.message.chat.id, f"""Готово...
        
Оцініть викладача в категорії: {categories[0]}""",parse_mode='HTML',reply_markup=markup)
    if callback_data_action == 'rateCategory':
        teacher = User.get_or_none(User.id == callback_data_id)
        rate = Rating.get_or_none(Rating.student_chat_id == query.message.chat.id,Rating.teacher_chat_id == teacher.chat_id,
                                  Rating.key == categories[int(callback_data_sum)])
        if rate:
            rate.value = callback_data_other
            rate.save()
        else:
            Rating(student_chat_id=query.message.chat.id,teacher_chat_id=teacher.chat_id,key=categories[int(callback_data_sum)],value=int(callback_data_other)).save()
        if len(categories) > int(callback_data_sum) + 1:
            markup = types.InlineKeyboardMarkup()
            ll = []
            for i in range(1,6):
                a = types.InlineKeyboardButton(
                    text=f"{i} ⭐",
                    callback_data=posts_cb.new(action="rateCategory",
                                               id=callback_data_id,
                                               sum=int(callback_data_sum)+1, other=i))
                ll.append(a)
            markup.add(*ll)
            await bot.send_message(query.message.chat.id, f"""Готово...
            
Оцініть викладача в категорії: {categories[int(callback_data_sum)+1]}""",parse_mode='HTML',reply_markup=markup)
        else:
            await bot.send_message(query.message.chat.id,"""Дякуємо за вашу оцінку. Це допоможе нам покращити рівень викладання предметів в нашому коледжі.""")

    if callback_data_action == 'rateByLikes':
        qry = Like.select(Like.teacher_chat_id, fn.Count().alias('count')).where(Like.value == 'like').group_by(Like.teacher_chat_id).order_by(SQL('count').desc()).limit(10)
        teachers = """"""
        for q in qry:
            teacher = User.get_or_none(User.chat_id == q.teacher_chat_id)
            teachers += f"📌 {teacher.full_name} - {teacher.speciality} - {q.count} 👍\n"
        await bot.send_message(query.message.chat.id,f"""Загальний рейтинг:

{teachers}""")

    if callback_data_action == 'rateByRate':
        qry = Rating.select(Rating.teacher_chat_id, fn.AVG(Rating.value).alias('rating')).where(Rating.key == categories[int(callback_data_id)]).group_by(Rating.teacher_chat_id).order_by(SQL('rating').desc()).limit(10)
        teachers = """"""
        for q in qry:
            teacher = User.get_or_none(User.chat_id == q.teacher_chat_id)
            teachers += f"📌 {teacher.full_name} - {teacher.speciality} - {q.rating} ⭐\n"
        await bot.send_message(query.message.chat.id,f"""Рейтинг "{categories[int(callback_data_id)]}":

{teachers}""")


@dp.message_handler(state='*', commands=['start'])
async def start_state(message: types.Message, state: FSMContext):
    await state.finish()
    await start_message(message)

@dp.message_handler(lambda message: message.text in teacher_menu,state='*')
async def menu_state(message: types.Message, state: FSMContext):
    await state.finish()
    await menu_list(message)
@dp.message_handler(lambda message: message.text in student_menu,state='*')
async def menu_state(message: types.Message, state: FSMContext):
    await state.finish()
    await menu_list(message)


@dp.message_handler(state=Send.send,content_types=types.ContentTypes.ANY)
async def send_state(message: types.Message, state: FSMContext):
    for i in User.select():
        try:
            await bot.copy_message(i.chat_id,message.chat.id,message.message_id)
        except:
            pass
    await state.finish()

@dp.message_handler(state=[RegTeacher.name,RegTeacher.subject,RegTeacher.info],content_types=types.ContentTypes.TEXT)
async def send_state(message: types.Message, state: FSMContext):
    if await state.get_state() == RegTeacher.name.state:
        await state.update_data(name=message.text)
        await bot.send_message(message.chat.id, """Додайте фото або аватар, який буде вас представляти.""",parse_mode='HTML')
        await RegTeacher.photo.set()
    elif await state.get_state() == RegTeacher.subject.state:
        await state.update_data(subject=message.text)
        await bot.send_message(message.chat.id, """Введіть коротку інформацію про себе (ваше бачення себе, улюблена цитата, побажання або щось на ваш вибір)""",parse_mode='HTML')
        await RegTeacher.info.set()
    elif await state.get_state() == RegTeacher.info.state:
        await state.update_data(info=message.text)
        markup = types.InlineKeyboardMarkup()
        ll = []
        for i in specialities:
            a = types.InlineKeyboardButton(
                text=i,
                callback_data=posts_cb.new(action="spec",
                                           id=i,
                                           sum=0, other=0))
            ll.append(a)
            if len(ll) == 2:
                markup.add(*ll)
                ll = []
        markup.add(*ll)
        user_data[str(message.chat.id)] = {"spec":set()}
        await bot.send_message(message.chat.id, """Оберіть спеціальності, на яких ви викладаєте.""",parse_mode='HTML',reply_markup=markup)
        await RegTeacher.speciality.set()


@dp.callback_query_handler(posts_cb.filter(action=["spec",'done']),state=RegTeacher.speciality)
async def select_spec(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    callback_data_action = callback_data['action']
    callback_data_id = callback_data['id']
    callback_data_sum = callback_data['sum']
    callback_data_other = callback_data['other']
    if callback_data_action == 'spec':
        if callback_data_id in user_data[str(query.message.chat.id)]['spec']:
            user_data[str(query.message.chat.id)]['spec'].remove(callback_data_id)
        else:
            user_data[str(query.message.chat.id)]['spec'].add(callback_data_id)
        markup = types.InlineKeyboardMarkup()
        ll = []
        for i in specialities:
            a = types.InlineKeyboardButton(
                text=i + ' ✅' if i in user_data[str(query.message.chat.id)]['spec'] else i,
                callback_data=posts_cb.new(action="spec",
                                           id=i,
                                           sum=0, other=0))
            ll.append(a)
            if len(ll) == 2:
                markup.add(*ll)
                ll = []
        markup.add(*ll)
        if user_data[str(query.message.chat.id)]['spec']:
            a = types.InlineKeyboardButton(
                text="Готово",
                callback_data=posts_cb.new(action="done",
                                           id=0,
                                           sum=0, other=0))
            markup.add(a)
        await bot.edit_message_reply_markup(query.message.chat.id,query.message.message_id,reply_markup=markup)
        await state.update_data(spec=user_data[str(query.message.chat.id)]['spec'])

    if callback_data_action == 'done':
        await bot.delete_message(message_id=query.message.message_id, chat_id=query.message.chat.id)
        user = User.get_or_none(User.chat_id == query.message.chat.id)
        user_data1 = await state.get_data()
        if not user:
            User(chat_id=query.message.chat.id,status='teacher',full_name=user_data1['name'],photo=user_data1['photo'],
                 subject=user_data1['subject'],info=user_data1['info'],speciality=','.join(user_data1['spec']),
                 reg_date=datetime.datetime.now(pytz.timezone('Europe/Kiev'))).save()
            await bot.send_message(query.message.chat.id, """Ваші дані збережено. Тепер ви можете переглянути свою анкету з результатами опитування. Також ви можете переглянути рейтинги викладачів на тих спеціальностях, на яких ви викладаєте.""",parse_mode='HTML',reply_markup=main_keyboard(query.message.chat.id))
            await state.finish()
        else:
            pass




@dp.message_handler(state=[RegTeacher.photo],content_types=types.ContentTypes.PHOTO)
async def photoaddd(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    await bot.send_message(message.chat.id,"""Введіть предмети, які ви викладаєте.""")
    await RegTeacher.subject.set()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

