from core.models import Comments, User, Channel
from core.forms import *
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.template import RequestContext
import json
from django.utils import timezone
import datetime

 
import redis
 
@login_required(login_url="login/")
def home(request):
    #comments = Comments.objects.select_related().all()[0:100]
    #return render(request, 'index.html', locals())
    lst = []
    lst1=[]
    #lst1 = Comments.objects.order_by().values('channel').distinct()
    cnl = Channel.objects.all()
    for i in cnl:
        if (str(request.user) in i.user_list[u'user'] or str(request.user) == i.admin) or request.user == i.admin:
            if i.channel_type == 'private':
                lst.append(i.channel_name)
        #print(i.user_list[u'user'])
    for i in cnl:
        if i.channel_type == 'general':
            lst1.append(i.channel_name)
    users = User.objects.all()

    print(lst)
    print(lst1)
    return render_to_response('home.html',{ 'user': request.user ,'room' : lst1,'p_room':lst,'access_user':users})
    
@csrf_exempt
def node_api(request):
    try:
        #Get User from sessionid
        session = Session.objects.get(session_key=request.POST.get('sessionid'))
        user_id = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=user_id)
        tms = datetime.datetime.now()
        #Create comment
        Comments.objects.create(user=user, text=request.POST.get('comment'), channel= request.POST.get('channel'),timestamp = tms)
        
        #Once comment has been created post it to the chat channel
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.publish('chat', str(request.POST.get('channel') +"~"+ user.username  + '*' + request.POST.get('comment')+'*' +str(tms.strftime("%b-%d-%Y %H:%M:%S")) ))
        
        return HttpResponse("Everything worked :)")
    except Exception as e:
        return HttpResponseServerError(str(e))
@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
            email=form.cleaned_data['email']
            )
            return HttpResponseRedirect('/register/success/')
    else:
        form = RegistrationForm()
    variables = RequestContext(request, {
    'form': form
    })
 
    return render_to_response(
    'registration/register.html',
    variables,
    )
 
def register_success(request):
    return render_to_response(
    'registration/success.html',
    )
 
def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')

# @login_required(login_url="login/")
# def login(request):
#     # login(request)
#     return render(request, 'registration/login.html',locals())
 
@login_required
def homes(request):
    return render_to_response(
    'home.html',
    { 'user': request.user }
    )

@login_required
def channel(request, chatroom):
    try:
        cnl = Channel.objects.get(channel_name=chatroom)
        if not (str(request.user) in cnl.user_list[u"user"] or request.user == cnl.admin):
            cnl.user_list[u"user"].append(str(request.user))
            cnl.save()
    except Channel.DoesNotExist:
        user_list={"user":[]}
        Channel.objects.create(admin=request.user,user_list=user_list, channel_name=chatroom,channel_type='general')
    cnl = Channel.objects.get(channel_name=chatroom)
    access_user = cnl.user_list[u"user"]
    chat = chatroom
    usr = request.user
    chnl_type = "general"
    comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
    for i in comments:
        print(i.timestamp)
    return render(request, 'index.html', locals())

@login_required
def p_channel(request, chatroom):
    try:
        cnl = Channel.objects.get(channel_name=chatroom)
        if str(request.user) in cnl.user_list[u"user"] or request.user == cnl.admin:
            comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
            chat = chatroom
            usr = request.user
            users = User.objects.all()
            usrr = [];
            for i in users:
                usrr.append(str(i))
            users = usrr 
            access_user = cnl.user_list[u"user"]
            print (access_user)
            print (users)
            access_user.append(str(cnl.admin))
            users1 = list(set(users) - set(access_user))
            chnl_type = "private"
            for i in comments:
                print(i.timestamp)
            return render(request, 'index.html', locals())
        else:
            return HttpResponseRedirect("/")
    except Channel.DoesNotExist:
        user_list={"user":[]}
        Channel.objects.create(admin=request.user,user_list=user_list, channel_name=chatroom, channel_type='private')
        comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
        chat = chatroom
        usr = request.user
        users = User.objects.all()
        usrr = [];
        for i in users:
            usrr.append(str(i))
        users = usrr 
        # user_to_add=[]
        access_user = [usr]
        print(access_user)
        cnl = Channel.objects.get(channel_name=chatroom)
        cnl.save()
        chnl_type = "private"
        access_user.append(str(cnl.admin))
        users1 = list(set(users) - set(access_user))
        return render(request, 'index.html', locals())

@login_required
def add_details(request,page_name):
    msg={}
    user = User.objects.all()
    if request.method == 'POST' and request.user in user:
        content = request.POST.get("content","")
        cate = request.POST.get("cate","")
        date = request.POST.get("date","")
        try:
            page = Page.objects.get(pk=page_name)
            page.content = content
            page.cate = cate
            page.date = date
            msg["status"]="200 OK"
        except Page.DoesNotExist:
            page = Page(name=page_name, content= content , cate = cate ,date = date)
            msg["status"]="201 Empty"
        page.save()
    else:
        msg["status"] = "202 Invalid"
    return JsonResponse(msg)
def add_users(request, chatroom):
    lst = []
    e = chatroom
    # cnl = Channel.objects.all()
    # for i in cnl:
    #     if (request.user in i.user_list[u'user'] or request.user == i.admin):
    #         lst.append(i.channel_name)
    # lst1 = Comments.objects.order_by().values('channel').distinct()
    users = User.objects.all()
    print(users)
    
    return render(request, 'add_users.html', locals())

@csrf_exempt
def add_user_to_private(request,chatroom):
    msg = {}
    try:
        if request.method == "POST":
            print(request.POST)
            cnl = Channel.objects.get(channel_name=chatroom)
            content = request.POST.getlist('lst[]')
            print(content)
            if isinstance(content, list):
                for i in content:
                    if not (i in cnl.user_list[u"user"]):
                        cnl.user_list[u"user"].append(i)
                cnl.save()
                msg["status"]="200 OK"
            else:
                msg["status"]="406 ERROR"
        else:
            msg["status"]="405 ERROR"
    except Channel.DoesNotExist:
        msg["status"]="404 ERROR"
    return JsonResponse(msg)





   	 

   	