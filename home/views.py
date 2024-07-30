import re
import uuid

import requests.exceptions
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.shortcuts import render, reverse

from utils import gen_random_code, bot_send_message
from .models import User, Member, Room, Message


def index(request):
    if not request.user.is_authenticated:
        return render(request, 'home/index.html')

    return HttpResponseRedirect(reverse('home:home_page'))


def home_page(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home:index'))

    context = {'rooms': [member.room for member in Member.objects.filter(user=request.user) if not member.left]}
    return render(request, 'home/home.html', context=context)


def room(is_ajax: bool):
    def view(request, invite_link):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('home:index'))

        try:
            r = Room.objects.get(invite_link=invite_link)
        except (Room.DoesNotExist, KeyError):
            messages.error(request, "There is no room with the Invite Link you provided. You can create one here.")
            return HttpResponseRedirect(reverse("home:create"))

        user_rooms = [member.room for member in Member.objects.filter(user=request.user)]
        if r not in user_rooms:
            m = Member(
                user=request.user,
                room=r,
                join_date=timezone.now(),
                is_admin=False,
                left=False
            )
            m.save()
        elif r in user_rooms and (m := Member.objects.get(room=r, user=request.user)).left:
            m.left = False
            m.save()
        preview_rooms = [member.room for member in Member.objects.filter(user=request.user) if not member.left]

        context = {
            'room': r,
            'recent_messages': r.message_set.all()[:200],
            'rooms': preview_rooms,
        }
        return render(request, 'home/chats-ajax.html' if is_ajax else 'home/chats.html', context=context)

    return view


def leave(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home:index'))
    if not request.POST:
        return Http404()

    try:
        m = Member.objects.get(user=request.user, room__id=request.POST["room-id"])
        m.left = True
        m.save()
        return HttpResponseRedirect(reverse('home:home_page'))
    except (KeyError, Member.DoesNotExist):
        return Http404("This room doesn't exist or you aren't joined.")


def create(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home:index'))

    if name := request.POST.get('name', None):
        invite_link = str(uuid.uuid4())
        r = Room(
            name=name,
            invite_link=invite_link,
            date_created=timezone.now(),
            creator=request.user
        )
        m = Member(
            user=request.user,
            room=r,
            join_date=timezone.now(),
            is_admin=True
        )
        r.save()
        m.save()
        return HttpResponseRedirect(reverse('home:room', args=(invite_link,)))

    context = {
        'is_creating': True,
        'rooms': [member.room for member in Member.objects.filter(user=request.user)]
    }
    return render(request, 'home/create.html', context=context)


def delete_room(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home:index'))
    if not request.POST:
        return Http404()
    r = Room.objects.get(id=request.POST['room-id'])
    if r.creator != request.user:
        return Http404("You are not the creator of this room.")

    r.delete()
    return HttpResponseRedirect(reverse('home:index'))


def send(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home:index'))
    if not request.POST:
        return Http404()

    r = Room.objects.get(invite_link=request.POST['room'])
    sender = Member.objects.get(user=request.user, room=r)
    text = request.POST["message"]

    if reply_id := request.POST.get("reply-id", ""):
        reply = Message.objects.get(id=reply_id)
    else:
        reply = None

    message = Message(sender=sender, text=text, room=r, date=timezone.now(), replied_message=reply)
    message.save()

    return HttpResponseRedirect(reverse('home:room', args=(r.invite_link,)))


def sign_up(request):
    if 'code' not in request.POST:
        username = request.POST['username']
        telegram_id = request.POST['telegram_id']
        if not re.findall('^[a-zA-Z][a-zA-Z0-9_]{4,30}$', username):
            messages.error(request, "Username must only have letters, numbers and underline. It must start with a letter and have at least 5 characters.")
            return HttpResponseRedirect(reverse('home:index'))
        if User.objects.filter(username=username, passed_login_code=True) or User.objects.filter(telegram_id=telegram_id, passed_login_code=True):
            messages.error(request, "A user with this username or Telegram ID already exists.")
            return HttpResponseRedirect(reverse('home:index'))

        try:
            code = gen_random_code()
            bot_send_message(telegram_id, "Your 'Chat Room' Login Code: %s" % code)

            signer = User(telegram_id=telegram_id, username=username, login_code=code, passed_login_code=False)
            signer.set_password(request.POST["password"])
            signer.save()

            messages.info(request, "The Telegram bot sent you the login code.")
            return HttpResponseRedirect(reverse('home:code', args=(signer.telegram_id, signer.username)))
        except requests.exceptions.HTTPError:
            messages.error(request, "An error occurred. Maybe you didn't start the bot.")
            return HttpResponseRedirect(reverse('home:index'))
        except Exception as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse('home:index'))

    else:
        signer = User.objects.get(username=request.POST['username'])
        if signer.passed_login_code:
            return HttpResponseRedirect(reverse("home:index"))
        if not signer.login_code == int(request.POST['code']):
            messages.error(request, 'The code is wrong. Try again.')
            return HttpResponseRedirect(reverse('home:code', args=(signer.telegram_id, signer.username)))
        else:
            signer.passed_login_code = True
            signer.save()
            messages.success(request, 'Created account! Now login with your username and password.')
            return HttpResponseRedirect(reverse('home:index'))


def login_view(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user and (user.passed_login_code or user.is_staff or user.is_superuser):
        login(request, user)
        return HttpResponseRedirect(reverse('home:home_page'))
    else:
        messages.error(request, "You entered a wrong username or password.")
        return HttpResponseRedirect(reverse('home:index'))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('home:index'))
