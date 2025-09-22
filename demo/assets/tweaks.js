"use strict";

function tweak_pair(pair_id) {
    let pair = document.getElementById(pair_id)
    let textarea = pair.querySelector("textarea")
    let button = pair.querySelector("button")
    textarea.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && event.shiftKey) {
            event.preventDefault()
            button.click();
        }
    })
    let setHeight = () => {
        textarea.style.height = "auto"
        textarea.style.height = (textarea.scrollHeight + 5) + "px"
        textarea.scrollIntoView({behavior: "smooth"})
    }
    textarea.addEventListener("input", setHeight)
    setHeight()
}

