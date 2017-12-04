VerifyUtil = {
    username: function(str) {
        let re = /^[0-9a-zA-Z\_]{6,16}$/;
        let result = re.exec(str)
        if (!result) {
            return '用户名需由6-16位数字、字母或下划线组成';
        } else {
            return null;
        }
    },
    password: function(str) {
        let re = /^[0-9a-zA-Z\_]{6,16}$/;
        let result = re.exec(str)
        if (!result) {
            return '密码需由6-16位数字、字母或下划线组成';
        } else {
            return null;
        }
    },
    email: function(str) {
        let re = /^[a-z_0-9.-]{1,64}@([a-z0-9-]{1,200}.){1,5}[a-z]{1,6}$/
        let result = re.exec(str)
        if (!result) {
            return '输入电子邮箱格式有误';
        } else {
            return null;
        }
    },
    comparePassword: function(str1, str2) {
        if (str1 !== str2) {
            return '两次密码输入不一致';
        } else {
            return null;
        }
    }
};
