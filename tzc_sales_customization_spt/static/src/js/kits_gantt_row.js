odoo.define('kits_tzc_project.kitsGanttRow', function (require) {
    "use strict";
    
    var kitsGanttRow = require('web_gantt.GanttRow');
    var _t = require('web.core')._t;
    
    var KitsGanttRow = kitsGanttRow.extend({
        /**
         * @param {integer|Array} value
         * @private
         */
        _getColor: function (value) {
            debugger;
            if (_.isNumber(value)) {
                if (Math.round(value) == 0){
                    value = 7;
                }
                return Math.round(value) % this.NB_GANTT_RECORD_COLORS;
            } 
            else 
            if (_.isArray(value)) {
                return value[0] % this.NB_GANTT_RECORD_COLORS;
            }
            return 0;
        },
    });
    
return KitsGanttRow;
});