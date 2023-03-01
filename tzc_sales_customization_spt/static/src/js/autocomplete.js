/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";

var rpc = require('web.rpc');
var ajax = require('web.ajax');
patch(AutoComplete.prototype, "tzc_sales_customization_spt.autocomplete", {
    selectOption(indices, params = {}) {
        var barcode = this.state.value;
        var c_props = this.props
        var inputRef =  this.inputRef.el
        var self = this
        var options = this.sources[indices[0]].options[indices[1]];
        if(barcode){
            rpc.query({
                model: 'product.product',
                method: 'get_product_name',
                args: [barcode]
            }).then(function(data) {
                // $.find('.o-autocomplete--input').value = data.product_name
                // $.find('.o-autocomplete--input').label = data.product_name
                // $.find('.o-autocomplete--input').name = data.product_name
                // $.find('.o-autocomplete--input').id =  data.product_id
                c_props.value = data.product_name
                options.label = data.product_name
                options.value = data.product_id
                debugger
                inputRef.value = data.product_name
                c_props.onSelect(options, {
                    ...params,
                    input: inputRef,
                });
            })
        }else{
            const option = this.sources[indices[0]].options[indices[1]];
            if (option.unselectable) {
                this.inputRef.el.value = "";
                this.close();
                return;
            }

            if (this.props.resetOnSelect) {
                this.inputRef.el.value = "";
            }

            this.forceValFromProp = true;
            this.props.onSelect(option, {
                ...params,
                input: this.inputRef.el,
            });
            const customEvent = new CustomEvent("AutoComplete:OPTION_SELECTED", { bubbles: true });
            this.root.el.dispatchEvent(customEvent);
            this.close();
        }
    }
})