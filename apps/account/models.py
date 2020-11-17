from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from apps.loon_base_model import BaseModel


class AppToken(BaseModel):
    """
    App token,用于api调用方授权
    """
    app_name = models.CharField('应用名称', max_length=50)
    token = models.CharField('签名令牌', max_length=50, help_text='后端自动生成')
    ticket_sn_prefix = models.CharField('工单流水号前缀', default='loonflow', max_length=20,
                                        help_text='工单流水号前缀，如设置为loonflow,则创建的工单的流水号为loonflow_201805130013')

    class Meta:
        verbose_name = '调用token'
        verbose_name_plural = '调用token'
        unique_together = ('app_name', )
