window.onload = function() {
    var modal = new Vue({
        el: '#modal-group',
        data: {
            url: '',
            isLoading: false,
            item: {},
            errorMsg: '',
            showingItem: {},
            showingSelectedPvs: [],
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
            multiSku: function(item) {
                if (Object.keys(item).length <= 0) { return false; }
                if (item.prices.length > 1) {
                    return true;
                }
                return false;
            },
            selectPvs: function(pvs, group_index) {
                Vue.set(this.showingSelectedPvs, group_index, pvs);
            },
            isPvsButtonDisable: function(pvs, group_index) {
                let previousPvs = '';
                let sep = ''
                for (i = 0; i < group_index; i++) {
                    if (this.showingSelectedPvs[i] != null || this.showingSelectedPvs[i] != undefined) {
                        previousPvs = previousPvs + sep + this.showingSelectedPvs[i];
                        sep = ';';
                    }
                }
                previousPvs = previousPvs + sep + pvs;
                for (i = 0; i < this.showingItem.prices.length; i++) {
                    let pricePvs = this.showingItem.prices[i];
                    if (pricePvs.pvs.startsWith(previousPvs)) {
                        return false;
                    }
                }
                return true;
            }
        },
        computed: {
            showError: function() {
                return this.errorMsg != null && this.errorMsg.trim() != '';
            },
            showingPrice: function() {
                if (Object.keys(this.showingItem).length <= 0) { return ''; }
                if (this.showingItem.prices.length == 1) { return '¥' + this.showingItem.prices[0].price; }
                let previousPvs = '';
                let sep = ''
                for (i = 0; i < this.showingSelectedPvs.length; i++) {
                    if (this.showingSelectedPvs[i] != null || this.showingSelectedPvs[i] != undefined) {
                        previousPvs = previousPvs + sep + this.showingSelectedPvs[i];
                        sep = ';';
                    }
                }
                for (i = 0; i < this.showingItem.prices.length; i++) {
                    let pricePvs = this.showingItem.prices[i];
                    if (pricePvs.pvs == previousPvs) {
                        return '¥' + pricePvs.price;
                    }
                }
                return '';
            },
        },
        filters: {
            showingPrice: function(item) {
                if (Object.keys(item).length <= 0) { return; }
                price = item.price;
                if (item.prices.length > 0) {
                    item.prices.forEach(function(info) {
                        if (info['pvs'] == 'def') {
                            price = info['price'];
                        }
                    });
                    if (parseFloat(price) == 0 || price == null) {
                        price = item.prices[0]['price'];
                    }
                }
                return price;
            },
        },
        watch: {
            showingItem: function(newItem){
                this.showingSelectedPvs = [];
            },
        }
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
                        console.log(response.data.data)
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
                }).catch(function(error){
                    itemList.isLoading = false;
                    itemList.errorMsg = '服务器异常';
                });
            },
            showDetail: function(item) {
                modal.showingItem = item;
                UIkit.modal('#modal-item-detail').show();
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
