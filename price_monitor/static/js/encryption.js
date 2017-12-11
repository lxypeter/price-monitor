Encrypt = {
    generateSign: function(params, dateStr, token) {
        let keys = Object.keys(params);
        keys = keys.sort();
        console.log(keys)
        let encodeString = token;
        for (let i = 0; i < keys.length; i = i + 1) {
            let val = params[keys[i]];
            if (val == null || val == undefined) {
                val ='';
            }
            val = JSON.stringify(val)
            encodeString = `${encodeString}${keys[i]}${val}`;
        }
        encodeString = `${encodeString}${dateStr}`;
        encodeString = CryptoJS.SHA1(encodeString).toString().toUpperCase();
        return encodeString;
    }
}
