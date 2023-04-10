/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";

var rpc = require("web.rpc");
var ajax = require("web.ajax");
patch(AutoComplete.prototype, "tzc_sales_customization_spt.autocomplete", {
  selectOption(indices, params = {}) {
    var barcode = this.state.value;
    var c_props = this.props;
    var inputRef = this.inputRef.el;
    var self = this;
    var options = this.sources[indices[0]].options[indices[1]];
    if (this.props.id === "product_id") {
      if (barcode) {
        rpc
          .query({
            model: "product.product",
            method: "get_product_name",
            args: [barcode],
          })
          .then(function (data) {
            if (data) {
              c_props.value = data.product_name;
              options.label = data.product_name;
              options.value = data.product_id;
              inputRef.value = data.product_name;
            }
          });
      }
      c_props.onSelect(options, {
        ...params,
        input: inputRef,
      });
    }
    else{
        this.forceValFromProp = true;
        this.props.onSelect(options, {
            ...params,
            input: this.inputRef.el,
        });
        this.close();
    }
  },
});
