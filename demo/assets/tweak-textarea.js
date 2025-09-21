"use strict";

//
// tweak textara behavior for in_id:
//     on shift-enter click trigger_id
//     resize height on every input
// arrange for this to run by using DeferScript
//

(() => {
    let params = new URL(document.currentScript.src).searchParams
    let in_id = params.get("in_id")
    let trigger_id = params.get("trigger_id")
    console.log(in_id, trigger_id)
    if (!in_id || !trigger_id)
        return;
    let ta = document.getElementById(in_id)
    ta.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && event.shiftKey) {
            event.preventDefault()
            document.getElementById(trigger_id).click();
        }
    })
    let setHeight = () => {
        ta.style.height = "auto"
        ta.style.height = (ta.scrollHeight + 5) + "px"
    }
    ta.addEventListener("input", setHeight)
    setHeight()
}) ()
    
