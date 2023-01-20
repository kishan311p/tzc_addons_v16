/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { isBinarySize } from "@web/core/utils/binary";
import { ImageField } from "@web/views/fields/image/image_field";
import { _lt } from "@web/core/l10n/translation";
import { url } from "@web/core/utils/urls";

const { Component, useState, onWillUpdateProps } = owl;
const { DateTime } = luxon;

export const fileTypeMagicWordMap = {
    "/": "jpg",
    R: "gif",
    i: "png",
    P: "svg+xml",
};
const placeholder = "/web/static/img/placeholder.png";

export function imageCacheKey(value) {
    if (value instanceof DateTime) {
        return value.ts;
    }
    return "";
}

patch(ImageField.prototype, "Image_Field", {
    
    getUrl(previewFieldName) {
        if (this.state.isValid && this.props.value) {
            if (isBinarySize(this.props.value)) {
                return url("/web/image", {
                    model: this.props.record.resModel,
                    id: this.props.record.resId,
                    field: previewFieldName,
                    unique: imageCacheKey(this.rawCacheKey),
                });
            } else if (this.props.type == 'char') {
                const magic = fileTypeMagicWordMap[this.props.value[0]] || "png";
                return `${this.props.value}`;

            } else {
                // Use magic-word technique for detecting image type
                const magic = fileTypeMagicWordMap[this.props.value[0]] || "png";
                return `data:image/${magic};base64,${this.props.value}`;
            }
        }
        return placeholder;
    },
    
    get hasTooltip() {
        return this.props.enableZoom && this.props.value;
        // return this.props.enableZoom && this.props.readonly && this.props.value;
    }
});
ImageField.supportedTypes = ["binary", "char"];
