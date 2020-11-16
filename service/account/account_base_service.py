import json

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from apps.account.models import AppToken
from service.base_service import BaseService
from service.common.log_service import auto_log


class AccountBaseService(BaseService):
    """
    account
    """

    @classmethod
    @auto_log
    def get_token_by_app_name(cls, app_name: str) -> tuple:
        """
        get app's call token by app_name
        :param app_name:
        :return:
        """
        app_token_obj = AppToken.objects.filter(app_name=app_name, is_deleted=0).first()
        return True, app_token_obj


    @classmethod
    @auto_log
    def app_workflow_permission_list(cls, app_name: str) -> tuple:
        """
        get app's authorised workflow_id list by app_name
        :param app_name:
        :return:
        """
        if not app_name:
            return False, 'app_name is not provided'
        if app_name == 'loonflow':
            # loonflow有权限访问所有workflow
            from apps.workflow.models import Workflow
            workflow_query_set = Workflow.objects.filter(is_deleted=0).all()
            workflow_id_list = []
            for workflow_obj in workflow_query_set:
                workflow_id_list.append(workflow_obj.id)
            return True, dict(workflow_id_list=workflow_id_list)

        app_token_obj = AppToken.objects.filter(app_name=app_name, is_deleted=0).first()
        if not app_token_obj:
            return False, 'appname is unauthorized'
        workflow_ids = app_token_obj.workflow_ids
        if workflow_ids:
            workflow_id_list = workflow_ids.split(',')
            workflow_id_list = [int(workflow_id) for workflow_id in workflow_id_list]
            return True, dict(workflow_id_list=workflow_id_list)
        else:
            return True, dict(workflow_id_list=[])

    @classmethod
    @auto_log
    def app_workflow_permission_check(cls, app_name: str, workflow_id: int) -> tuple:
        """
        appname has permission for workflow check by app_name and workflow_id
        :param app_name:
        :param workflow_id:
        :return:
        """
        if app_name == 'loonflow':
            return True, ''
        flag, result = cls.app_workflow_permission_list(app_name)

        if flag and result.get('workflow_id_list') and workflow_id in result.get('workflow_id_list'):
            return True, ''
        else:
            return False, 'the app has no permission to the workflow_id'

    @classmethod
    @auto_log
    def app_ticket_permission_check(cls, app_name: str, ticket_id: int) -> tuple:
        """
        appname has permission to ticket check by app_name and ticket_id
        :param app_name:
        :param ticket_id:
        :return:
        """
        from service.ticket.ticket_base_service import ticket_base_service_ins
        flag, ticket_obj = ticket_base_service_ins.get_ticket_by_id(ticket_id)
        if not flag:
            return False, ticket_obj
        workflow_id = ticket_obj.workflow_id
        permission_check, msg = cls.app_workflow_permission_check(app_name, workflow_id)
        if not permission_check:
            return False, msg
        return True, ''

    @classmethod
    @auto_log
    def get_token_list(cls, search_value: str, page: int = 1, per_page: int = 10) -> tuple:
        """
        get app permission token list
        :param search_value: support app name fuzzy queries
        :param page:
        :param per_page:
        :return:
        """
        query_params = Q(is_deleted=False)
        if search_value:
            query_params &= Q(app_name__contains=search_value)
        token_objects = AppToken.objects.filter(query_params)
        paginator = Paginator(token_objects, per_page)
        try:
            token_result_paginator = paginator.page(page)
        except PageNotAnInteger:
            token_result_paginator = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results
            token_result_paginator = paginator.page(paginator.num_pages)
        token_result_object_list = token_result_paginator.object_list
        token_result_object_format_list = []
        for token_result_object in token_result_object_list:
            token_result_object_format_list.append(token_result_object.get_dict())
        return True, dict(token_result_object_format_list=token_result_object_format_list,
                          paginator_info=dict(per_page=per_page, page=page, total=paginator.count))

    @classmethod
    @auto_log
    def add_token_record(cls, app_name: str, ticket_sn_prefix: str, workflow_ids: str, username: str) -> tuple:
        """
        add app token record
        :param app_name:
        :param ticket_sn_prefix:
        :param workflow_ids:
        :param username:
        :return:
        """
        import uuid
        token = uuid.uuid1()
        app_token_obj = AppToken(app_name=app_name, ticket_sn_prefix=ticket_sn_prefix, workflow_ids=workflow_ids,
                                 token=token, creator=username)
        app_token_obj.save()
        return True, dict(app_token_id=app_token_obj.id)

    @classmethod
    @auto_log
    def update_token_record(cls, app_token_id: int, app_name: str, ticket_sn_prefix: str, workflow_ids: str) -> tuple:
        """
        update token record
        :param app_token_id:
        :param app_name:
        :param ticket_sn_prefix:
        :param workflow_ids:
        :return:
        """
        app_token_obj = AppToken.objects.filter(id=app_token_id, is_deleted=0).first()
        if not app_token_obj:
            return False, 'record is not exist or has been deleted'
        app_token_obj.app_name = app_name
        app_token_obj.ticket_sn_prefix = ticket_sn_prefix
        app_token_obj.workflow_ids = workflow_ids
        app_token_obj.save()
        return True, ''

    @classmethod
    @auto_log
    def del_token_record(cls, app_token_id: int) -> tuple:
        """
        del app token record
        :param app_token_id:
        :return:
        """
        app_token_obj = AppToken.objects.filter(id=app_token_id, is_deleted=0).first()
        if not app_token_obj:
            return False, 'record is not exist or has been deleted'
        app_token_obj.is_deleted = True
        app_token_obj.save()
        return True, ''

    @classmethod
    @auto_log
    def admin_permission_check(cls, username: str = '', user_id: int = 0) -> tuple:
        """
        admin permission check
        :param username:
        :param user_id:
        :return:
        """
        if username:
            flag, result = cls.get_user_by_username(username)
        elif user_id:
            flag, result = cls.get_user_by_user_id(user_id)
        else:
            return False, 'username or user_id is needed'
        if flag is False:
            return False, result
        if result.is_admin:
            return True, 'user is admin'
        else:
            return False, 'user is not admin'

    @classmethod
    @auto_log
    def workflow_admin_permission_check(cls, username: str = '', user_id: int = 0) -> tuple:
        """
        workflow admin permission check
        :param username:
        :param user_id:
        :return:
        """
        if username:
            flag, result = cls.get_user_by_username(username)
        elif user_id:
            flag, result = cls.get_user_by_username(username)
        else:
            return False, 'username or user_id is needed'
        if flag is False:
            return False, result
        if result.is_workflow_admin:
            return True, 'user is workflow admin'
        if result.is_admin:
            return True, 'user is admin'
        else:
            return False, 'user is not admin or workflow admin'

    @classmethod
    @auto_log
    def admin_or_workflow_admin_check(cls, username: str = '', user_id: int = 0) -> tuple:
        """
        admin or workflow admin check
        :param username:
        :param user_id:
        :return:
        """
        if username:
            flag, result = cls.get_user_by_username(username)
        elif user_id:
            flag, result = cls.get_user_by_username(username)
        else:
            return False, 'username or user_id is needed'
        if flag is False:
            return False, result
        if result.is_workflow_admin or result.is_admin:
            return True, 'user is admin or workflow admin'
        else:
            return False, 'user is not admin or workflow admin'

    @classmethod
    @auto_log
    def reset_password(cls, username: str = '', user_id: int = 0) -> tuple:
        """
        reset user's password
        just admin or workflow admin need login loonflow's admin,so just admin and workflow admin can rest password
        :param username:
        :param user_id:
        :return:
        """
        flag, result = False, ''
        if username:
            flag, result = cls.get_user_by_username(username)
        if user_id:
            flag, result = cls.get_user_by_user_id(user_id)

        if flag:
            user_obj = result
            if user_obj.is_admin or user_obj.is_workflow_admin:
                password_str = make_password('123456', None, 'pbkdf2_sha256')
                user_obj.password = password_str
                user_obj.save()
                return True, 'password has been reset to 123456'
            else:
                return False, 'just admin or workflow admin can be reset password'
        else:
            return False, result


account_base_service_ins = AccountBaseService()
