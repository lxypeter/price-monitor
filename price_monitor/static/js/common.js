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

DateUtil = {
    currentTimeStr: function() {
        const data = new Date();
        const year = data.getFullYear();
        const mon = data.getMonth() + 1;
        const monStr = mon < 10 ? `0${mon}` : `${mon}`;
        const day = data.getDate();
        const dayStr = day < 10 ? `0${day}` : `${day}`;
        const hour = data.getHours();
        const hourStr = hour < 10 ? `0${hour}` : `${hour}`;
        const minutes = data.getMinutes();
        const minutesStr = minutes < 10 ? `0${minutes}` : `${minutes}`;
        const seconds = data.getSeconds();
        const secondsStr = seconds < 10 ? `0${seconds}` : `${seconds}`;
        return `${year}-${monStr}-${dayStr} ${hourStr}:${minutesStr}:${secondsStr}`;
    }
}

SignFetch = {
    post: function(url, data, token) {
        dateStr = DateUtil.currentTimeStr();
        sign = Encrypt.generateSign(data, dateStr, token)
        headers = { 'date-str': dateStr, 'sign': sign };
        return axios.post(url, data, { 'headers': headers });
    }
} 
