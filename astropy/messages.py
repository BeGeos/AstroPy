from email.message import EmailMessage
# Messages for API

messages = {
    'welcome': 'This is AstroPy',
    'no argument': 'No argument passed in',
    'not found': 'No record found',
    'hello': 'Hello, There',
    'bad request': '400 Bad request',
    'no coordinates': 'No coordinates provided',
    'invalid password': 'Invalid password',
    'invalid user': 'Invalid user',
    'required arguments': 'Required arguments not provided'
}


# Email replies
# -- Email for verification code
class ReplyMessage:

    def __init__(self, sender, receiver, username, security_code=None, recovery_link=None):
        self.sender = sender
        self.receiver = receiver
        self.username = username
        self.security_code = security_code
        self.recovery_link = recovery_link

    def verification_msg(self):
        verification_code_msg = EmailMessage()
        verification_code_msg['Subject'] = '[AstroPy] - Please confirm you email address'
        verification_code_msg['From'] = self.sender
        verification_code_msg['To'] = self.receiver
        verification_code_msg.set_content(f"""Hey {self.username}!\n 
Thank you for signing up. 
To complete the procedure and finally get to use this API, send a post request to the link below, and make sure 
to include in the body your username and the security code\n\n
Link: http://localhost:5000/astropy/api/v1/verification
Security code: {self.security_code}\n\n
This code will be active for 10 minutes, after that you can request a new one at the following link\n
http://localhost:5000/astropy/api/v1/new-code-request\n
In that case send a post request specifying in the body your username and password, a new email like this 
one will be sent promptly with a new security code.\n\n
If you did not send this request to sign up, your email address might have been used illicitly.\n\n
Thank you very much for your cooperation and support. I am extremely grateful that you decided to use this 
service. I hope you find it useful and it can enhance your astronomical observation experience.\n\n
\n\nThanks,\n@BeGeos - AstroPy""")

        return verification_code_msg

    def recovery_msg(self):
        recovery_msg = EmailMessage()
        recovery_msg['Subject'] = '[AstroPy] - Password recovery request'
        recovery_msg['From'] = self.sender
        recovery_msg['To'] = self.receiver
        recovery_msg.set_content(f"""Hey {self.username}!\n  
It seems like somebody made a request to recover/change your password.
If you want to update the password send a post request to the link below. In the body of your request, 
include your username and the new password.\n\n
Link: {self.recovery_link}\n
This link will be active for 24 hours, after that you can request a new one at the following link
http://localhost:5000/astropy/api/v1/recovery\nand follow the steps for recovering your password.\n
In case you did not send any request but still received this message, your username and email were used illicitly.
\nYou could either skip this message or if you were worried about security issues contact this link\n
http://localhost/astropy/security
\n\nThanks,\n@BeGeos - AstroPy""")

        return recovery_msg
