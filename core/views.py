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
    return HttpResponseRedirect('/channel/general')
    
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
def add_channel(request):
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
    
    return render_to_response('add_channel.html',{ 'chnl_type' : "general",  'user' : request.user,'room' : lst1,'p_room' : lst })

@login_required
def add_pchannel(request):

    lst = []
    lst1=[]
    cnl = Channel.objects.all()
    usr = request.user
    for i in cnl:
        if (str(request.user) in i.user_list[u'user'] or str(request.user) == i.admin) or request.user == i.admin:
            if i.channel_type == 'private':
                lst.append(i.channel_name)
        
    for i in cnl:
        if i.channel_type == 'general':
            lst1.append(i.channel_name)
    return render_to_response('add_channel.html',{ 'chnl_type' : "private" , 'user' : request.user,'room' : lst1,'p_room' : lst })

@login_required
def channel(request, chatroom):
    # if len(chatroom)==0:
    #     if len(Channel.objects.get(channel_name="general"))== 0:
    #         Channel.objects.create(admin="Collab Bot",user_list=user_list, channel_name="general",channel_type='general')
    #     else:
    #         chatroom="general"

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
    access_user.append(str(cnl.admin))
    chat = chatroom
    usr = request.user
    chnl_type = "general"
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
    room = lst1
    p_room = lst
    comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
    last = ""
    new_comments= []
    for i in range(len(comments)):
        temp = {}
        temp["user"] = comments[i].user
        temp["text"] = comments[i].text
        temp["timestamp"] = comments[i].timestamp
        temp["last"] = False
        if(comments[i].user == last):
            temp["last"] = True
        else:
            last = comments[i].user
            temp["last"] = False
        new_comments.append(temp)

    last_comment_user = str(comments[(len(comments)-1)].user)
    return render(request, 'home.html', locals())

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
            access_user.append(str(cnl.admin))
            users1 = list(set(users) - set(access_user))
            chnl_type = "private"
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
            room = lst1
            p_room = lst
            return render(request, 'home.html', locals())
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
        access_user = [str(usr)]
        cnl = Channel.objects.get(channel_name=chatroom)
        cnl.save()
        chnl_type = "private"
        users1 = list(set(users) - set(access_user))
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
        room = lst1
        p_room = lst
        return render(request, 'home.html', locals())

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





   	 

   	