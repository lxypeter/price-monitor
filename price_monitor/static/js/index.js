window.onload = function() {
    var modal = new Vue({
        el: '#modal-group',
        data: {
            url: '',
            isLoading: false,
            item: {},
            errorMsg: '',
        },
        methods: {
            confirmUrl: function() {
                this.isLoading = true;
                const data = {
                    'url': this.url,
                };
                SignFetch.post('/api/sign/url/analysis', data, this.$refs.token.value).then(function(response) {
                    modal.isLoading = false;
                    if (response.data.result_code == 0) {
                        modal.item = response.data.data;
                    } else {
                        modal.errorMsg = response.data.msg;
                    }
                }).catch(function(error){
                    modal.isLoading = false;
                    modal.errorMsg = '服务器异常';
                });
            },
            submitItem: function() {
                SignFetch.post('/api/sign/item/store', this.item, this.$refs.token.value).then(function(response) {
                    modal.isLoading = false;
                    if (response.data.result_code == 0) {
                        itemList.loadItems()
                        UIkit.modal('#modal-group-2').hide();
                    } else {
                        modal.errorMsg = response.data.msg
                    }
                }).catch(function(error){
                    modal.isLoading = false;
                    modal.errorMsg = '服务器异常';
                });
            },
        },
        computed: {
            showError: function() {
                return this.errorMsg != null && this.errorMsg.trim() != '';
            },
            multiSku: function() {
                if (Object.keys(this.item).length <= 0) { return false; }
                if (this.item.stock_info.length > 1) {
                    return true;
                }
                return false;
            },
        },
        filters: {
            showingPrice: function(item) {
                if (Object.keys(item).length <= 0) { return; }
                price = item.price;
                if (item.stock_info.length > 0) {
                    item.stock_info.forEach(function(info) {
                        if (info['pvs'] == 'def') {
                            price = info['price'];
                        }
                    });
                    if (parseFloat(price) == 0) {
                        price = item.stock_info[0]['price'];
                    }
                }
                return price;
            },
        },
    });

    var itemList = new Vue({
        el: '#item_list',
        data: {
            url: '',
            isLoading: false,
            items: [],
            errorMsg: '',
        },
        methods: {
            loadItems: function() {
                this.isLoading = true;
                SignFetch.post('/api/sign/item/list', {}, this.$refs.token.value).then(function(response) {
                    itemList.isLoading = false;
                    if (response.data.result_code == 0) {
                        itemList.items = response.data.data;
                    }
                }).catch(function(error){
                    itemList.isLoading = false;
                    itemList.errorMsg = '服务器异常';
                });
            },
            disconnectItem: function(item) {
                result = confirm('确定删除"' + item.name + '"吗？');
                if (!result) { return; }
                SignFetch.post('/api/sign/item/disconnection', item, this.$refs.token.value).then(function(response) {
                    if (response.data.result_code == 0) {
                        itemList.loadItems()
                    }
                    console.log(response.data.data);
                }).catch(function(error){
                    itemList.isLoading = false;
                    itemList.errorMsg = '服务器异常';
                });
            },
        },
        filters: {
            showingPrice: function(item) {
                if (Object.keys(item).length <= 0) { return; }
                price = '0.00';
                if (item.prices.length > 0) {
                    item.prices.forEach(function(info) {
                        if (info['pvs'] == 'def') {
                            price = info['price'];
                        }
                    });
                    if (parseFloat(price) == 0) {
                        price = item.prices[0]['price'];
                    }
                }
                return price;
            },
            mallImage: function(mallType) {
                switch (mallType){
                    case 'T':
                        return {
                            'background-image': 'url(/static/images/taobao.jpg)',
                        };
                    case 'TM':
                        return {
                            'background-image': 'url(/static/images/tmall.jpg)',
                        };
                }
            },
        },
    });
    itemList.loadItems();
}
