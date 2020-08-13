from django.shortcuts import render
from django.db.models import Q
from django.db import models
from django.shortcuts import render
from django.http import JsonResponse
from account.models import MyUser, Team, TeamMember
from django.db.utils import IntegrityError
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
import simplejson
import json


# Create your views here.

def isleader(request):
    # request中必须包含'Team_id'字段
    userid = request.session.get('_auth_user_id')
    data = simplejson.loads(request.body)
    team = Team.objects.get(t_id=data['Team_id'])
    if userid == str(team.create_user.id):
        return True
    else:
        return False


def backend_remove_member(request):
    # request中必须包含'tm_id'字段
    data = simplejson.loads(request.body)
    try:
        record = TeamMember.objects.get(tm_id=data['tm_id'])
        record.delete()
        return JsonResponse({'success': True, 'exc': ''})
    except TeamMember.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'record does not exist.'})


def get_team_name(request):
    # POST(json)
    # 发送：
    # -Team_id：整型，表示团队id
    #
    # 接收：
    # -Team_name： 字符串，表示团队名称
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    try:
        team = Team.objects.get(t_id=data['Team_id'])
        return JsonResponse({'Team_name': team.t_name, 'success': True, 'exc': ''})
    except Team.DoesNotExist:
        return JsonResponse({'success': False, 'exc': ''})


def invite_members(request):
    # POST(json)
    # 发送：
    # -Inviter_id：整型，表示邀请者id
    # -User_id：整型，表示被邀请者id
    # -Team_id：整型，表示邀请至的团队id
    #
    # 收到：
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    if request.user.is_authenticated:
        # 只有在团队里的人才能发送邀请
        try:
            team = Team.objects.get(t_id=data['Team_id'])
            # 是创建者可以邀请
            if data['Inviter_id'] == team.create_user.id:
                pass
            else:
                try:
                    # 是成员可以邀请
                    teammember = TeamMember.objects.get(t_id=data['Team_id'], u_id=data['Inviter_id'], status=2)
                except TeamMember.DoesNotExist:
                    return JsonResponse({'success': False, 'exc': 'you are not in this team.'})
        except Team.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'the team does not exist.'})

        try:
            myuser = MyUser.objects.get(id=data['User_id'])
            try:
                # 如果已经是成员，就不能被邀请了
                exist = TeamMember.objects.get(u_id=data['User_id'], t_id=data['Team_id'], status=2)
                return JsonResponse({'success': False, 'exc': 'the user is in your team.'})
            except TeamMember.DoesNotExist:
                # 没加入，就能被邀请，每次join_time字段更新
                try:
                    # 之前邀请过
                    exist = TeamMember.objects.get(u_id=data['User_id'], t_id=data['Team_id'])
                    exist.inviter.id = data['Inviter_id']
                    exist.save()
                    return JsonResponse({'success': True, 'exc': 'invite again'})
                except TeamMember.DoesNotExist:
                    # 没邀请过
                    team = Team.objects.get(t_id=data['Team_id'])
                    record = TeamMember.objects.create(t_id=team, u_id=myuser, inviter_id=data['Inviter_id'])
                    return JsonResponse({'success': True, 'exc': ''})
        except MyUser.DoesNotExist:
            return JsonResponse({'success': False, 'exc': 'you invite an unknown user.'})
    else:
        return JsonResponse({'success': False, 'exc': 'user should login first.'})


def disband(request):
    pass


def deal_with_application(request):
    # POST(json)
    # 发送：
    # Team_id：表示用户正申请加入的团队
    # User_id：表示申请者
    # Accepted: 布尔值，表示创建者是否通过申请
    #
    # 收到：
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': 'you should login first.'})
    if not isleader(request):
        return JsonResponse({'success': False, 'exc': 'you are not the leader of the team'})
    data = simplejson.loads(request.body)

    try:
        record = TeamMember.objects.get(t_id=data['Team_id'], u_id=data['User_id'])
    except TeamMember.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'unknown application.'})

    if data['Accepted']:
        record.status = 2
        record.save()
        return JsonResponse({'success': True, 'exc': ''})
    else:
        # 拒绝就删除申请
        record.delete()
        return JsonResponse({'success': False, 'exc': 'application is declined.'})


def members_in_team(request):
    # POST(json)
    #
    # 发送：
    # -Team_id：整型，表示查询的团队id
    #
    # 接收：
    # -Member_list: [{User_id, User_avatar, User_name, User_status}, ...]：数组，其中每个元素为
    # {用户id，用户头像，用户名，用户身份（字符串，创建者为‘管理员’，其他为‘成员’）}，例如：[{123, ‘media / UserAvatar / 123.j
    # pg’, ’张三’, ‘管理员’}, {1234, ‘media / UserAvatar / 1234.j
    # pg’, ’李四’, ‘成员’}, …]
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': 'you should login first.'})
    try:
        team = Team.objects.get(t_id=data['Team_id'])
        leader = MyUser.objects.get(id=team.create_user.id)
        info = {
            'User_id': leader.id,
            'User_avatar': leader.u_avatar.url,
            'User_name': leader.username,
            'User_status': '管理员'
        }
        returnlist = []
        returnlist.append(info)
        print(returnlist)
        result = TeamMember.objects.filter(Q(t_id=data['Team_id']) & Q(status=2) & ~Q(u_id=leader.id))
        tmplist = list(result.values('u_id').distinct())

        if tmplist is not None:
            for member in tmplist:
                myuser = MyUser.objects.get(id=member['u_id'])
                info = {
                    'User_id': myuser.id,
                    'User_avatar': myuser.u_avatar.url,
                    'User_name': myuser.username,
                    'User_status': '成员'
                }
                returnlist.append(info)
        return JsonResponse({'Member_list': returnlist, 'success': True, 'exc': ''})
    except Team.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'the team does not exist.'})


def remove_member(request):
    # POST(json)
    # 发送：
    # -Team_id：整型，表示要删除队员的团队id
    # -User_id：整型，表示被删除的队员id
    #
    # 收到：
    # -success：布尔值，表示是否成功
    # -exc：字符串，表示错误信息，成功则为空
    data = simplejson.loads(request.body)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'exc': ''})
    try:
        team = Team.objects.get(t_id=data['Team_id'])
    except Team.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'the team does not exist.'})
    try:
        member = MyUser.objects.get(id=data['User_id'])
    except MyUser.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'the user doex not exist.'})
    # 如果是队长，不能直接退出
    if team.create_user.id == member.id:
        return JsonResponse({'success': False, 'exc': 'the leader cannot pull off directly.'})
    # 如果是成员，可以退出
    try:
        record = TeamMember.objects.get(t_id=data['Team_id'], u_id=data['User_id'], status=2)
        record.delete()
        # 还要对文件操作吗
        return JsonResponse({'success': True, 'exc': ''})
    except TeamMember.DoesNotExist:
        return JsonResponse({'success': False, 'exc': 'you are not in the team.'})


def list_my_invitations(request):
    data = simplejson.loads(request.body)
    if not request.user.is_authenticated:
        return JsonResponse({"Invitation_list": [], "success": False, "exc": "please login or register"})
    result = TeamMember.objects.filter(Q(u_id__id__exact=data['User_id']) & Q(status__exact=1))
    returnList = []
    for invitation in result:
        temp = {"Team_name": invitation.t_id.t_name, "Team_id": invitation.t_id.t_id,
                "User_name": invitation.inviter.username}
        returnList.append(temp)
    return JsonResponse({"Invitation_list": returnList, "success": True, "exc": ""})
