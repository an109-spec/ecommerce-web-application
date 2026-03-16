/* =========================
FUNCTIONS (không cần bọc)
========================= */
function generateCode(){
const prefix="SALE"
const random=Math.random()
.toString(36)
.substring(2,8)
.toUpperCase()
document.getElementById("code").value =
prefix + random
}
/* =========================
CREATE VOUCHER
========================= */
async function createVoucher(){

const name = document.getElementById("name").value
const code = document.getElementById("code").value
const type = document.getElementById("discount_type").value
const value = document.getElementById("discount_value").value
const usage = document.getElementById("usage_limit").value
const min = document.getElementById("min_order_value").value
const start = document.getElementById("start_time").value
const end = document.getElementById("end_time").value

/* lấy sản phẩm */
let variants = []
document.querySelectorAll("input[name='variant_ids[]']:checked")
.forEach(el => variants.push(el.value))
try {
const res = await fetch("/seller/api/voucher/create",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
name:name,
code:code,
discount_type:type,
discount_value:value,
usage_limit:usage,
min_order_value:min,
start_time:start,
end_time:end,
variant_ids: variants
})
})

const data = await res.json()

if(data.success){
alert("Tạo voucher thành công")
window.location="/seller/vouchers"
}else{
alert(data.message || "Có lỗi xảy ra")
}
} catch (error) {
alert("Không thể tạo voucher, vui lòng thử lại")
}
}

/* VALIDATE FORM */
function validateVoucher(){

const code=document.getElementById("code").value
const value=document.querySelector("[name='discount_value']").value

if(code===""){
alert("Voucher code không được để trống")
return false
}

if(value<=0){
alert("Giá trị giảm phải > 0")
return false
}

return true
}

/* NUMBER TO VIETNAMESE TEXT */

function numberToVietnamese(num){

const units = ["","một","hai","ba","bốn","năm","sáu","bảy","tám","chín"]

function readThree(n){

let hundred = Math.floor(n/100)
let ten = Math.floor((n%100)/10)
let unit = n%10

let str=""

if(hundred>0) str+=units[hundred]+" trăm "

if(ten>1){
str+=units[ten]+" mươi "
if(unit==1) str+="mốt"
else if(unit==5) str+="lăm"
else if(unit>0) str+=units[unit]
}

else if(ten==1){
str+="mười "
if(unit==5) str+="lăm"
else if(unit>0) str+=units[unit]
}

else if(unit>0){
str+=units[unit]
}

return str.trim()

}

const million = Math.floor(num/1000000)
const thousand = Math.floor((num%1000000)/1000)
const rest = num%1000

let result=""

if(million>0) result+=readThree(million)+" triệu "
if(thousand>0) result+=readThree(thousand)+" nghìn "
if(rest>0) result+=readThree(rest)

return result

}

document.addEventListener("DOMContentLoaded",()=>{

function bindMoneyText(inputId, textId){

const input=document.getElementById(inputId)
const text=document.getElementById(textId)

if(!input) return

input.addEventListener("input",function(){

const value=parseInt(this.value)

if(!value){
text.innerHTML=""
return
}

text.innerHTML="≈ "+numberToVietnamese(value)

})

}

bindMoneyText("discount_value","discount_text")
bindMoneyText("min_order_value","min_text")

})

