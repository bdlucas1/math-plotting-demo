"use strict";

function tweak_textarea(in_id, trigger_id) {
    let ta = document.getElementById(in_id)
    ta.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && event.shiftKey) {
            event.preventDefault()
            let e = document.getElementById(trigger_id)
            console.log("triggering", e)
            e.click();
        }
    })
    let setHeight = () => {
        ta.style.height = "auto"
        ta.style.height = (ta.scrollHeight + 5) + "px"
        ta.scrollIntoView()
    }
    ta.addEventListener("input", setHeight)
    setHeight()
}
    
