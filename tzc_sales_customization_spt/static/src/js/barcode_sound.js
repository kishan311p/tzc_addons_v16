
(function () {
    var _catch = Promise.prototype.catch;
    Promise.prototype.guardedCatch = function (onRejected) {
        return _catch.call(this, function (reason) {
            debugger;
            const error = (reason instanceof Error && "cause" in reason) ? reason.cause : reason;
            if(error.message.data.message.length){
                var str_msg = error.message.data.message.match("Scanned");
                if (str_msg) {
                    var src = "/tzc_sales_customization_spt/static/src/sounds/error.wav";
                    $('body').append('<audio src="' + src + '" autoplay="true"></audio>');
                }
            }
            if (!error || !(error instanceof Error)) {
                if (onRejected) {
                    onRejected.call(this, reason);
                }
            }
            return Promise.reject(reason);
        });
    };
})();
