import json

from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from service.account.account_base_service import account_base_service_ins
from service.format_response import api_response
from apps.loon_base_view import LoonBaseView
from schema import Schema, Regex, And, Or, Use, Optional

from service.permission.manage_permission import manage_permission_check


@method_decorator(login_required, name='dispatch')
class LoonAppTokenView(LoonBaseView):
    post_schema = Schema({
        'app_name': And(str, lambda n: n != '', error='app_name is needed'),
        Optional('ticket_sn_prefix'): str,
        'workflow_ids': And(str, lambda n: n != '', error='workflow_ids is needed'),
    })

    @manage_permission_check('admin')
    def get(self, request, *args, **kwargs):
        """
        call api permission
        调用权限列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        request_data = request.GET
        search_value = request_data.get('search_value', '')
        per_page = int(request_data.get('per_page', 10))
        page = int(request_data.get('page', 1))
        flag, result = account_base_service_ins.get_token_list(
            search_value, page, per_page)
        if flag is not False:
            paginator_info = result.get('paginator_info')
            data = dict(value=result.get('token_result_object_format_list'), per_page=paginator_info.get('per_page'),
                        page=paginator_info.get('page'), total=paginator_info.get('total'))
            code, msg, = 0, ''
        else:
            code, data = -1, ''
        return api_response(code, msg, data)

    @manage_permission_check('admin')
    def post(self, request, *args, **kwargs):
        """
        add call api permission
        新增调用权限记录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        json_str = request.body.decode('utf-8')
        request_data_dict = json.loads(json_str)
        app_name = request_data_dict.get('app_name', '')
        ticket_sn_prefix = request_data_dict.get('ticket_sn_prefix', '')
        workflow_ids = request_data_dict.get('workflow_ids', '')
        username = request.user.username
        flag, result = account_base_service_ins.add_token_record(
            app_name, ticket_sn_prefix, workflow_ids, username)
        if flag is False:
            code, data = -1, {}
        else:
            code, data = 0, {'id': result.get('app_token_id')}

        return api_response(code, result, data)


@method_decorator(login_required, name='dispatch')
class LoonAppTokenDetailView(LoonBaseView):
    patch_schema = Schema({
        'app_name': And(str, lambda n: n != '', error='app_name is needed'),
        Optional('ticket_sn_prefix'): str,
        'workflow_ids': And(str, lambda n: n != '', error='workflow_ids is needed'),
    })

    @manage_permission_check('admin')
    def patch(self, request, *args, **kwargs):
        """
        编辑token
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        app_token_id = kwargs.get('app_token_id')
        json_str = request.body.decode('utf-8')
        request_data_dict = json.loads(json_str)
        app_name = request_data_dict.get('app_name', '')
        ticket_sn_prefix = request_data_dict.get('ticket_sn_prefix', '')
        workflow_ids = request_data_dict.get('workflow_ids', '')
        flag, msg = account_base_service_ins.update_token_record(
            app_token_id, app_name, ticket_sn_prefix, workflow_ids)
        if flag is False:
            code, data = -1, {}
        else:
            code, data = 0, {}

        return api_response(code, msg, data)

    @manage_permission_check('admin')
    def delete(self, request, *args, **kwargs):
        """
        删除记录
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        app_token_id = kwargs.get('app_token_id')
        flag, msg = account_base_service_ins.del_token_record(app_token_id)
        if flag is False:
            code, data = -1, {}
        else:
            code, data = 0, {}
        return api_response(code, msg, data)


class LoonLoginView(LoonBaseView):
    def post(self, request, *args, **kwargs):
        """
        登录验证
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        json_str = request.body.decode('utf-8')
        if not json_str:
            return api_response(-1, 'patch参数为空', {})
        request_data_dict = json.loads(json_str)
        username = request_data_dict.get('username', '')
        password = request_data_dict.get('password', '')
        try:
            user = authenticate(username=username, password=password)
        except Exception as e:
            return api_response(-1, e.__str__(), {})

        if user is not None:
            login(request, user)
            return api_response(0, '', {})
        else:
            return api_response(-1, 'username or password is invalid', {})


class LoonLogoutView(LoonBaseView):
    def get(self, request, *args, **kwargs):
        """
        注销
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        logout(request)
        return redirect('/manage')
