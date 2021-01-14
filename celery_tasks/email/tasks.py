from celery import Task
from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.main import celery_app

# 监听整个任务的钩子
class Mytask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print('task success 11111')
        return super(Mytask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('task failed')
        # 可以记录到程序中或者任务队列中,让celery尝试重新执行
        return super(Mytask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        print('this is after return')
        return super(Mytask, self).after_return(status, retval, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        print('this is retry')
        return super(Mytask,self).on_retry(exc, task_id, args, kwargs, einfo)


@celery_app.task(name='send_verify_email', base=Mytask)
def send_verify_email(username, token, email):
    # 发邮件
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的账户<br><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
    username, token, token)
    sender = settings.EMAIL_FROM
    receiver = [email]
    send_mail(subject, message, sender, receiver, html_message=html_message)




