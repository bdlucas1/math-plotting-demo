"use strict";

//
// use with Python exec_js(js) in a layout to arrange for js to be executed after the layout is loaded
// see code for examples
//
// TODO: this is a bit hacky - can we do better?
//

(() => {
    let js = new URL(document.currentScript.src).searchParams.get("js")
    if (js) {
        console.log("eval: " + js)
        eval(js)
    }
}) ()
    
