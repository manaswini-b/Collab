from core.models import Comments, User, Channel
from core.forms import *
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.template import RequestContext
 
import redis
 
@login_required
def home(request):
    #comments = Comments.objects.select_related().all()[0:100]
    #return render(request, 'index.html', locals())
    lst = []
    cnl = Channel.objects.all()
    for i in cnl:
        if (request.user in i.user_list[u'user'] or request.user == i.admin) and i.channel_type == 'private':
            lst.append(i.channel_name)
    lst1 = Comments.objects.order_by().values('channel').distinct()
    users = User.objects.all()
    return render_to_response('home.html',{ 'user': request.user ,'room' : lst1,'p_room':lst,'access_user':users})
    
@csrf_exempt
def node_api(request):
    try:
        #Get User from sessionid
        session = Session.objects.get(session_key=request.POST.get('sessionid'))
        user_id = session.get_decoded().get('_auth_user_id')
        user = User.objects.get(id=user_id)
 
        #Create comment
        Comments.objects.create(user=user, text=request.POST.get('comment'), channel= request.POST.get('channel'))
        
        #Once comment has been created post it to the chat channel
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.publish('chat', request.POST.get('channel') +"~"+ user.username  + ': ' + request.POST.get('comment'))
        
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
    comments = Comments.objects.filter(channel__contains = chatroom)[0:100]
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
            access_user = cnl.user_list
            print (access_user)
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
        access_user = [usr]
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
class CronForm(forms.Form):
    user_names = forms.ModelChoiceField(queryset=Comments.objects.all().order_by().values('user').distinct())
def user_select_channel(request):
	form = CronForm()
	if request.method == "POST":
		form = CronForm(request.POST)
		if form.is_valid:
			#redirect to the url where you'll process the input
			return HttpResponseRedirect("/p_channel") # insert reverse or url
	errors = form.errors or None
	return render(request, 'user_select.html',{
          'form': form,
          'errors': errors,
   })
   	 

   	