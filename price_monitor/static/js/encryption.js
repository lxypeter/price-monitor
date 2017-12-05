Encrypt = {
    generateSign: function(params, dateStr, token) {
        let keys = Object.keys(params);
        keys = keys.sort();
        let encodeString = token;
        for (let i = 0; i < keys.length; i = i + 1) {
          const val = params[keys[i]];
          encodeString = `${encodeString}${keys[i]}${val}`;
        }
        encodeString = `${encodeString}${dateStr}`;
        encodeString = CryptoJS.SHA1(encodeString).toString().toUpperCase();
        return encodeString;
    }
}
