from django.shortcuts import render
from django.views.decorators.http import (require_GET,
                                          require_POST)
from django.http import HttpResponse, JsonResponse
from account.models import Comment, MyUser
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from doc.views import get_identity
from account.models import MyUser, File, Team, Template, TeamMember, Favorites
import simplejson
from datetime import datetime


@require_POST
def add_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先注册或登录。"})

    try:
        data = simplejson.loads(request.body)
        doc_id = data['doc_id']
    except Exception:
        return JsonResponse({'success': False, 'exc': "请求格式错误。"})

    try:
        doc = File.objects.get(f_id=doc_id)
        fav = Favorites.objects.create(u_id=request.user, f_id=doc)
        return JsonResponse({'success': True, 'exc': ''})
    except Exception:
        return JsonResponse({'success': False, 'exc': '文档ID有误。'})


@require_POST
def cancel_doc(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先注册或登录。"})
    try:
        data = simplejson.loads(request.body)
        doc_id = data['doc_id']
    except Exception:
        return JsonResponse({'success': False, 'exc': "请求格式错误。"})
    try:
        doc = File.objects.get(f_id=doc_id)
        fav = Favorites.objects.get(u_id=request.user, f_id=doc)
        fav.delete()
        return JsonResponse({'success': True, 'exc': ''})
    except Exception:
        return JsonResponse({'success': False, 'exc': '文档ID有误。'})


@require_GET
def get_all_docs(request):
    """by lighten 
    "list":收藏的文档列表
    \[
    {
        "doc\_id":文档id
        "title":字符串，文档标题
        "team\_id":所属团队id，若没有则-1
        "team\_name":字符串，所属团队名
        "time":字符串，最后编辑时间
    },
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "exc": "请先注册或登录。"})
    try:
        favs = Favorites.objects.filter(u_id=request.user)
        res = []
        for fav in favs:
            if fav.f_id.trash_status==False:
                if fav.f_id.t_id == None:
                    temp = {
                        "doc_id": fav.f_id.f_id,
                        "title": fav.f_id.f_title,
                        'creator': fav.f_id.u_id.username,
                        "team_id": -1,
                        "team_name": "",
                        "time": fav.f_id.f_etime.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                else:
                    temp ={
                        "doc_id": fav.f_id.f_id,
                        "title": fav.f_id.f_title,
                        'creator': fav.f_id.u_id.username,
                        "team_id": fav.f_id.t_id.t_id,
                        "team_name": fav.f_id.t_id.t_name,
                        "time": fav.f_id.f_etime.strftime('%Y-%m-%d %H:%M:%S'),  
                    }
                res.append(temp)
        return JsonResponse({'success': True, 'exc': '', 'list': res})
    except Exception:
        return JsonResponse({'success': False, 'exc': '文档ID有误。'})
