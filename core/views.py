from core.models import Comments, User, Channel
from core.forms import *
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.template import RequestContext
from .forms import UploadFileForm
import json
from django.utils import timezone
from datetime import datetime
from html.parser import HTMLParser
import redis
import urllib.parse
import sys
import zipfile,time
from pytz import timezone


@csrf_exempt
def upload(request):
    if request.method == 'POST':
      form = UploadFileForm(request.POST, request.FILES)
      if form.is_valid():
        users_id={}
        for filename,content in fileiterator(request.FILES["file"]):
            #print(filename)
            if filename == "users.json":
                anc = json.loads(content.decode('utf-8'))            
                for i in anc:
                    User.objects.create_user(i["name"],i["name"]+"@demo.com","demo123")
                    users_id[i["id"]]=i["name"]
        channels_list=[]
        channels_id={}
        for filename,content in fileiterator(request.FILES["file"]):
            if filename == "channels.json":
                tmp = json.loads(content.decode('utf-8'))
                # print (tmp)
                #print(users_id)
                for j in tmp:
                    channels_list.append(j["name"])
                    channels_id[j["id"]] = j["name"]
                    creator = users_id[j["creator"]] 
                    user_list=[]
                    temp_list = j["members"]
                    for k in temp_list:
                        user_list.append(users_id[k])
                    if creator in user_list:
                        user_list.remove(creator)
                    if j["is_general"]:
                        chnl_type = "public"
                    else:
                        chnl_type = "private"
                    Channel.objects.create(admin= User.objects.get(username=creator),user_list={"user":user_list}, channel_name=j["name"],channel_type=chnl_type)
                                # print(content)
        for filename,content in fileiterator(request.FILES["file"]):
            print(filename)
            for l in channels_list:
                #print(l)
                dmy = filename.split("/")
                if dmy[0] == l and dmy[1]:
                    ancc = json.loads(content.decode('utf-8'))            
                    for i in ancc:
                        # print(ancc.encode("utf-8"))
                        if "user" in i: 
                            cookie_datetime = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(int(i["ts"].split(".")[0])))
                            tms=str(cookie_datetime)
                            print(i["user"])
                            user=users_id[i["user"]]
                            txt=str(cleanupString(i["text"]))
                            re1='(<)'   # Any Single Character 1
                            re2='(.)'  # Any Single Character 2
                            re3='((?:[a-z][a-z]*[0-9]+[a-z0-9]*))'  # Alphanum 1
                            re4='(\\|)' # Any Single Character 3
                            re5='([-a-z0-9\._]*)' # Word 1
                            re6='(>)'   # Any Single Character 4
                            rg = re.compile(re1+re2+re3+re4+re5+re6,re.IGNORECASE|re.DOTALL)
                            items = re.findall(rg,txt)
                            for item in items:
                                txt = txt.replace(''.join(item), item[4])
                            re1='(<)'   # Any Single Character 1
                            re2='(@)'  # Any Single Character 2
                            re3='((?:[a-z][a-z]*[0-9]+[a-z0-9]*))'  # Alphanum 1
                            re6='(>)'   # Any Single Character 4
                            rg = re.compile(re1+re2+re3+re6,re.IGNORECASE|re.DOTALL)
                            items = re.findall(rg,txt)
                            for item in items:
                                txt = txt.replace(''.join(item), users_id[item[2]])
                            Comments.objects.create(user=User.objects.get(username = user), text=txt, channel= l,timestamp = tms)
                        else:
                            break
                    
        return HttpResponseRedirect('/?msg=upload_successful')
    else:
        form = UploadFileForm()
    return render_to_response('upload.html', {'form': form})
 
def fileiterator(zipf):
    with zipfile.ZipFile(zipf, "r", zipfile.ZIP_STORED) as openzip:
        filelist = openzip.infolist()
        for f in filelist:
            yield(f.filename, openzip.read(f))

def cleanupString(string):
    string = urllib.parse.unquote(string)
    return HTMLParser().unescape(string).encode(sys.getfilesystemencoding()).decode("utf-8", errors="ignore")

@login_required(login_url="login/")
def home(request):
    return HttpResponseRedirect('/channel/collab_general')
    
@csrf_exempt
def node_api(request):
    try:
        #Get User from sessionid
        session = Session.objects.get(session_key=request.POST.get('sessionid'))
        user_id = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=user_id)
        now = datetime.now()
        tms = timezone('Asia/Kolkata').localize(now)
        print(request.POST.get('comment'))
        print(request.POST.get('channel'))
        #Create comment
        Comments.objects.create(user=user, text=request.POST.get('comment'), channel= request.POST.get('channel'),timestamp = tms)
        #for i in Comments.objects.get(timestamp=tms):
        #   print(i)
        #Once comment has been created post it to the chat channel
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.publish('chat', str(request.POST.get('channel') +"~"+ str(user.username)  + '*' + request.POST.get('comment')+'*' +str(tms.strftime("%b.%d,%Y, %I:%M %p.")) ))
        print(str(user)+request.POST.get('comment'))
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
    usr = request.user
    for i in cnl:
        if (str(request.user) in i.user_list[u'user'] or str(request.user) == i.admin) or request.user == i.admin:
            if i.channel_type == 'private':
                lst.append(i.channel_name)
        #print(i.user_list[u'user'])
    for i in cnl:
        if i.channel_type == 'public':
            lst1.append(i.channel_name)
    usr = request.user
    users = User.objects.all()
    usrr = [];
    for i in users:
        usrr.append(str(i))
    users = usrr 
    access_user = [str(usr)]
    users1 = list(set(users) - set(access_user))
    return render_to_response('add_channel.html',{ 'chnl_type' : "public",  'user' : request.user,'room' : lst1,'p_room' : lst, 'users1' : users1})

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
        if i.channel_type == 'public':
            lst1.append(i.channel_name)
    usr = request.user
    users = User.objects.all()
    usrr = [];
    for i in users:
        usrr.append(str(i))
    users = usrr 
    access_user = [str(usr)]
    users1 = list(set(users) - set(access_user))
    return render_to_response('add_channel.html',{ 'chnl_type' : "private" , 'user' : request.user,'room' : lst1,'p_room' : lst, 'users1' : users1})

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
        Channel.objects.create(admin=request.user,user_list=user_list, channel_name=chatroom,channel_type='public')
    cnl = Channel.objects.get(channel_name=chatroom)
    access_user = cnl.user_list[u"user"]
    access_user.append(str(cnl.admin))
    print(access_user)
    chat = chatroom
    usr = request.user
    chnl_type = "public"
    lst = []
    lst1=[]
    users = User.objects.all()
    usrr = []
    for i in users:
        usrr.append(str(i))
    users = usrr 
    req_user = [str(usr)]
    users1 = list(set(users) - set(access_user))
    #lst1 = Comments.objects.order_by().values('channel').distinct()
    cnl = Channel.objects.all()
    for i in cnl:
        if (str(request.user) in i.user_list[u'user'] or str(request.user) == i.admin) or request.user == i.admin:
            if i.channel_type == 'private':
                lst.append(i.channel_name)
        #print(i.user_list[u'user'])
    for i in cnl:
        if i.channel_type == 'public':
            lst1.append(i.channel_name)
    room = lst1
    p_room = lst
    comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
    last = ""
    new_comments= []
    for i in range(len(comments)):
        temp = {}
        temp["user"] = comments[i].user
        comments_temp = str(cleanupString(comments[i].text))
        temp_text = comments_temp.split("^")
        temp["text"] = cleanupString(temp_text[0])
        if(len(temp_text) > 1):
            if(temp_text[1] == "sni"):
                temp["type"] = "sni"
            elif(temp_text[1] == "doc"):
                temp["type"] = "doc"
                temp["url"] = temp_text[2]
        else:
            temp["type"] = "text"
        temp["timestamp"] = comments[i].timestamp
        temp["last"] = False
        if(comments[i].user == last):
            temp["last"] = True
        else:
            last = comments[i].user
            temp["last"] = False
        new_comments.append(temp)
    if len(comments)>1:
        last_comment_user = str(comments[(len(comments)-1)].user)
    return render(request, 'home.html', locals())

@login_required
def p_channel(request, chatroom):
    try:
        cnl = Channel.objects.get(channel_name=chatroom)
        if not (str(request.user) in cnl.user_list[u"user"] or request.user == cnl.admin):
            cnl.user_list[u"user"].append(str(request.user))
            cnl.save()
    except Channel.DoesNotExist:
        user_list={"user":[]}
        Channel.objects.create(admin=request.user,user_list=user_list, channel_name=chatroom,channel_type='private')
    cnl = Channel.objects.get(channel_name=chatroom)
    access_user = cnl.user_list[u"user"]
    access_user.append(str(cnl.admin))
    cnl_admin = cnl.admin
    print(access_user)
    chat = chatroom
    usr = request.user
    users = User.objects.all()
    usrr = []
    for i in users:
        usrr.append(str(i))
    users = usrr 
    req_user = [str(usr)]
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
        if i.channel_type == 'public':
            lst1.append(i.channel_name)
    room = lst1
    p_room = lst
    comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
    last = ""
    new_comments= []
    for i in range(len(comments)):
        temp = {}
        temp["user"] = comments[i].user
        comments_temp = str(cleanupString(comments[i].text))
        temp_text = comments_temp.split("^")
        temp["text"] = cleanupString(temp_text[0])
        if(len(temp_text) > 1):
            if(temp_text[1] == "sni"):
                temp["type"] = "sni"
            elif(temp_text[1] == "doc"):
                temp["type"] = "doc"
                temp["url"] = temp_text[2]
        else:
            temp["type"] = "text"
        temp["timestamp"] = comments[i].timestamp
        temp["last"] = False
        if(comments[i].user == last):
            temp["last"] = True
        else:
            last = comments[i].user
            temp["last"] = False
        new_comments.append(temp)
    if len(comments)>1:
        last_comment_user = str(comments[(len(comments)-1)].user)
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

@csrf_exempt
def check_add_channel(request,chatroom):
    msg={}
    channel_name = chatroom
    if request.method == "POST":
        cnl = Channel.objects.all()
        temp=[]
        for i in cnl:
            temp.append(i.channel_name) 
        print (channel_name)
        if channel_name in temp:
            msg["status"]="Channel already available"
        else:
            msg["status"]="200 OK"
    else:
        msg["status"]="405 ERROR"
    print (msg)
    return JsonResponse(msg)

@csrf_exempt
def new_channel(request):
    if request.method == "POST":
        page_name=request.POST['page_name']
        users_in_channel=request.POST.getlist('select_user[]')
        user_list={"user":users_in_channel}
        Channel.objects.create(admin=request.user,user_list=user_list, channel_name=str(page_name),channel_type='public')
        return HttpResponseRedirect('/channel/'+page_name+'/')
    else:
        return HttpResponseRedirect('/add_channel/')


@csrf_exempt
def new_pchannel(request):
    if request.method == "POST":
        page_name=request.POST['page_name']
        users_in_channel=request.POST.getlist('select_user[]')
        user_list={"user":users_in_channel}
        Channel.objects.create(admin=request.user,user_list=user_list, channel_name=str(page_name),channel_type='private')
        return HttpResponseRedirect('/p_channel/'+page_name+'/')
    else:
        return HttpResponseRedirect('/add_pchannel/')

   	