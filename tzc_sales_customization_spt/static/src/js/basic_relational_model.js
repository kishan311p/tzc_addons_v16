
/* @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Record, RelationalModel } from "@web/views/basic_relational_model";
import {
    mapWowlValueToLegacy,
    mapViews,
    mapActiveFieldsToFieldsInfo,
} from "@web/views/legacy_utils";

patch(Record.prototype, "tzc_sales_customization_spt.basic_relational_model", {
    async update(changes) {
        if (this.batchingUpdateProm) {
            // Assign changes in the current batch
            Object.assign(this.batchChanges, changes);
            return this._updatePromise;
        }

        this.batchingUpdateProm = Promise.resolve();
        this.batchChanges = Object.assign({}, changes);

        let resolveUpdatePromise;
        this._updatePromise = new Promise((r) => {
            resolveUpdatePromise = r;
        });

        await this.batchingUpdateProm;
        changes = this.batchChanges;
        this.batchingUpdateProm = null;
        this.batchChanges = null;

        const data = {};
        for (const [fieldName, value] of Object.entries(changes)) {
            debugger;
            if (this.fields['body_html'] == undefined){
                this.fields['body_html'] = {
                    "change_default": false,
                    "name": "body_html",
                    "readonly": false,
                    "required": false,
                    "sanitize": false,
                    "sanitize_tags": true,
                    "searchable": true,
                    "sortable": true,
                    "store": true,
                    "string": "Body",
                    "translate": false,
                    "type": "html",
                    "onChange": "1"
                }
            }
            const fieldType = this.fields[fieldName].type;
            data[fieldName] = mapWowlValueToLegacy(value, fieldType);
            // special case for many2ones: they can be updated with a new name (e.g. if edited from
            // the dialog), but in the basic_model it worked differently, we had a datapoint for the
            // many2one value and we reloaded it directly. In the new model, we directly update the
            // value [id, display_name], so we reload beforehand, in the many2one field itself. In
            // the next few lines, we thus manually apply the renaming on the legacy datapoint.
            if (this.fields[fieldName].type === "many2one" && Array.isArray(changes[fieldName])) {
                const newName = changes[fieldName][1];
                if (newName || newName === "") {
                    const bm = this.model.__bm__;
                    const m2oDatapointId = bm.get(this.__bm_handle__).data[fieldName].id;
                    const m2oDatapoint = bm.localData[m2oDatapointId];
                    if (m2oDatapoint && m2oDatapoint.data.id === changes[fieldName][0]) {
                        m2oDatapoint.data.display_name = newName;
                    }
                }
            }
            // same for reference fields
            if (this.fields[fieldName].type === "reference" && changes[fieldName].displayName) {
                const bm = this.model.__bm__;
                const m2oDatapointId = bm.get(this.__bm_handle__).data[fieldName].id;
                const m2oDatapoint = bm.localData[m2oDatapointId];
                if (m2oDatapoint) {
                    m2oDatapoint.data.display_name = changes[fieldName].displayName;
                }
            }
        }
        if (this._urgentSave) {
            const fieldNames = await this.model.__bm__.notifyChanges(this.__bm_handle__, data, {
                viewType: this.__viewType,
                notifyChange: false,
            });
            resolveUpdatePromise();
            this._removeInvalidFields(fieldNames);
            this.__syncData();
            return;
        }

        const parentID = this.model.__bm__.localData[this.__bm_handle__].parentID;
        if (parentID && this.__viewType === "list") {
            // inside an x2many (parentID is the id of the static list datapoint)
            const mainRecordId = this.model.__bm__.localData[parentID].parentID;
            const mainRecordDP = this.model.__bm__.localData[mainRecordId];
            const mainRecordValues = { ...mainRecordDP.data, ...mainRecordDP._changes };
            const x2manyFieldName = Object.keys(mainRecordValues).find(
                (name) => mainRecordValues[name] === parentID
            );
            if (!x2manyFieldName) {
                throw new Error("couldn't find x2many field name");
            }
            const operation = { operation: "UPDATE", id: this.__bm_handle__, data };
            const prom = this.__syncParent(operation);
            prom.catch(resolveUpdatePromise);
            await prom;
        } else {
            const prom = this.model.__bm__.notifyChanges(this.__bm_handle__, data, {
                viewType: this.__viewType,
            });
            prom.catch(resolveUpdatePromise); // onchange rpc may return an error
            const fieldNames = await prom;
            this._removeInvalidFields(fieldNames);
            for (const fieldName of fieldNames) {
                if (["one2many", "many2many"].includes(this.fields[fieldName].type)) {
                    const { editedRecord } = this.data[fieldName];
                    if (editedRecord) {
                        editedRecord._removeAllInvalidFields();
                    }
                }
            }
            this.__syncData();
        }
        this._removeInvalidFields(Object.keys(changes));
        this.model.notify();
        resolveUpdatePromise();
    }
})