document.addEventListener("DOMContentLoaded",()=>{
const flashInput = document.getElementById("flashPrice")
if(flashInput){
flashInput.addEventListener("input", function(){
    const flash = this.value
    if(!selectedVariantPrice) return
    const percent = Math.round((1 - flash / selectedVariantPrice) * 100)
    document.getElementById("discountPercentInput").value = percent
  })
}

function buildStockAllocation(variantElements, totalStock){
  const variants = Array.from(variantElements).map((el) => ({
    id: el.value,
    available: parseInt(el.dataset.stock || "0", 10),
    stockLimit: 0,
  }))

  let remaining = totalStock

  // chia đều trước
  variants.forEach((variant, idx) => {
    const variantsLeft = variants.length - idx
    const target = Math.ceil(remaining / variantsLeft)
    const allocated = Math.min(target, variant.available)
    variant.stockLimit = allocated
    remaining -= allocated
  })

  // dồn phần còn lại vào các variant còn sức chứa
  if(remaining > 0){
    for(const variant of variants){
      if(remaining <= 0) break
      const extraCapacity = variant.available - variant.stockLimit
      if(extraCapacity <= 0) continue
      const extra = Math.min(extraCapacity, remaining)
      variant.stockLimit += extra
      remaining -= extra
    }
  }

if(remaining > 0){
throw new Error("Không đủ tồn kho khả dụng để phân bổ số lượng Flash Sale")
}

  return variants.filter((v) => v.stockLimit > 0)
}

window.createFlashSale = async function(){
  const variants = document.querySelectorAll("input[name='variant_ids[]']:checked")

  if(variants.length === 0){
    alert("Phải chọn ít nhất 1 phân loại")
    return
  }

  const percent = document.getElementById("discountPercentInput").value
  const stock = parseInt(document.getElementById("stock").value, 10)

  const start = document.querySelector("[name='start_time']").value
  const end = document.querySelector("[name='end_time']").value
  if(!percent || !start || !end || Number.isNaN(stock)){
    alert("Vui lòng nhập đầy đủ thông tin trước khi tạo Flash Sale")
    return
  }

  if(Number.isNaN(stock) || stock <= 0){
    alert("Vui lòng nhập số lượng Flash Sale hợp lệ")
    return
  }

  if(Number(percent) <= 0 || Number(percent) >= 100){
    alert("Phần trăm giảm phải lớn hơn 0 và nhỏ hơn 100")
    return
  }

  if(new Date(start) >= new Date(end)){
    alert("Thời gian kết thúc phải lớn hơn thời gian bắt đầu")
    return
  }

  if(stock > selectedVariantStock){
    alert("Số lượng flash sale vượt tồn kho")
    return
  }

  let allocations
  try {
    allocations = buildStockAllocation(variants, stock)
  } catch (err) {
    alert(err.message)
    return
  }

  for(const item of allocations){
    const res = await fetch(FLASH_SALE_CREATE_URL, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        variant_id: item.id,
        discount_percent: percent,
        stock_limit: item.stockLimit,
        start_time: start,
        end_time: end,
      }),
    })

    if(!res.ok){
      let message = "Tạo flash sale thất bại"
      try {
        const payload = await res.json()
        if(payload?.message) message = payload.message
      } catch (_) {}
      alert(message)
      return
    }
  }

  window.location.href = "/seller/flash-sales"
}

///xóa flash sale

document.addEventListener("click", async (e) => {
const btn = e.target.closest("[data-delete]")
if(!btn) return
e.preventDefault()
const ok = confirm("⚠ Bạn chắc chắn muốn xóa Flash Sale này?")
if(!ok) return
const url = btn.dataset.url
if(!url) return
try{
const res = await fetch(url,{ method:"POST" })
if(res.ok){
alert("✅ Xóa thành công")
window.location.reload()
}else{
alert("❌ Xóa thất bại")
}
}catch(err){
console.error(err)
alert("Server lỗi")
}
})
})

///
///cập nhật flash sale
///
async function updateFlashSale(id){

const percent=document.getElementById("discountPercentInput").value
const stock=parseInt(document.getElementById("stock").value)

const start=document.querySelector("[name='start_time']").value
const end=document.querySelector("[name='end_time']").value

const url = FLASH_UPDATE_URL.replace("0", id)

const res = await fetch(url,{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
discount_percent:percent,
stock_limit:stock,
start_time:start,
end_time:end
})

})

if(res.ok){

alert("Cập nhật thành công")

window.location="/seller/flash-sales"

}else{

alert("Update thất bại")

}

}