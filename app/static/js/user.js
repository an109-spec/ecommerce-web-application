/* =========================
STATUS MESSAGE
========================= */
console.log("USER JS START");
function setStatus(msg, err = false) {

    const el = document.getElementById("status-message")
    el.textContent = msg
    el.style.color = err ? "red" : "green"

}


/* =========================
API HELPER
========================= */

async function api(url, method = "GET", body = null) {

    const opt = { method, headers: {} }

    if (body) {
        opt.headers["Content-Type"] = "application/json"
        opt.body = JSON.stringify(body)
    }

    const r = await fetch(url, opt)

    const text = await r.text()

    let data

    try {
        data = JSON.parse(text)
    } catch {
        throw new Error("Server không trả JSON: " + text.substring(0,120))
    }

    if (!r.ok) throw new Error(data.error || "API error")

    return data
}


/* =========================
DOM
========================= */

const btnEditProfile = document.getElementById("btn-edit-profile")
const btnCancelEditProfile = document.getElementById("btn-cancel-edit-profile")
const btnSaveProfile = document.getElementById("btn-save-profile")

const btnUploadAvatar = document.getElementById("btn-upload-avatar")
const avatarFile = document.getElementById("avatar-file")
const avatarPreview = document.getElementById("avatar-preview")

const btnChangePassword = document.getElementById("btn-change-password")
const currentPassword = document.getElementById("current-password")
const newPassword = document.getElementById("new-password")

const btnLoadOrders = document.getElementById("btn-load-orders")

const btnAddAddress = document.getElementById("btn-add-address")
const modal = document.getElementById("address-modal")
const btnCloseAddress = document.getElementById("btn-close-address")
const btnSaveAddress = document.getElementById("btn-save-address")

const addrName = document.getElementById("addr-name")
const addrPhone = document.getElementById("addr-phone")
const addrCity = document.getElementById("addr-city")
const addrDistrict = document.getElementById("addr-district")
const addrWard = document.getElementById("addr-ward")
const addrLine = document.getElementById("addr-line")
const addrDefault = document.getElementById("addr-default")


/* =========================
EDIT PROFILE
========================= */

function toggleEdit(on) {

    document.getElementById("view-profile-section")
        .classList.toggle("hidden", on)

    document.getElementById("edit-profile-section")
        .classList.toggle("hidden", !on)

}


/* =========================
RENDER ADDRESS
========================= */

function renderAddresses(list) {

    const box = document.getElementById("profile-addresses")
    box.innerHTML = ""

    if (!list.length) {

        box.innerHTML = "<p>Chưa có địa chỉ</p>"
        return

    }

    list.forEach((a) => {

        const div = document.createElement("div")
        div.className = "address-card"

        const left = document.createElement("div")
        left.className = "address-text"

        left.innerHTML = `
        ${a.full_name} | ${a.phone}<br>
        ${a.address_line}, ${a.ward}, ${a.district}, ${a.city}
        ${a.is_default ? '<span class="tag-default">Mặc định</span>' : ''}
        `

        const right = document.createElement("div")
        right.className = "address-actions"

        const d = document.createElement("button")
        d.textContent = "Đặt mặc định"
        d.className = "btn outline"
        d.onclick = () => setDefault(a.id)

        const x = document.createElement("button")
        x.textContent = "Xóa"
        x.className = "btn outline"
        x.onclick = () => deleteAddr(a.id)

        right.appendChild(d)
        right.appendChild(x)

        div.appendChild(left)
        div.appendChild(right)

        box.appendChild(div)

    })

}


/* =========================
RENDER PROFILE
========================= */

function renderProfile(data) {

    document.getElementById("profile-username").textContent = data.username
    document.getElementById("profile-email").textContent = data.email
    document.getElementById("profile-phone").textContent = data.phone
    document.getElementById("profile-full-name").textContent = data.profile?.full_name || "-"
    document.getElementById("profile-birthday").textContent = data.profile?.birthday || "-"

    renderAddresses(data.profile?.addresses || [])

    document.getElementById("edit-username").value = data.username || ""
    document.getElementById("edit-email").value = data.email || ""
    document.getElementById("edit-phone").value = data.phone || ""
    document.getElementById("edit-full-name").value = data.profile?.full_name || ""
    document.getElementById("edit-birthday").value = data.profile?.birthday || ""

    if (data.avatar)
        avatarPreview.src = data.avatar

}


/* =========================
LOAD PROFILE
========================= */

async function loadProfile() {

    const d = await api("/user/profile")
    renderProfile(d)

}


/* =========================
EDIT PROFILE EVENTS
========================= */

if (btnEditProfile)
btnEditProfile.onclick = () => toggleEdit(true)

if (btnCancelEditProfile)
btnCancelEditProfile.onclick = async () => {

    await loadProfile()
    toggleEdit(false)

}

if (btnSaveProfile)
btnSaveProfile.onclick = async () => {

    try {

        const payload = {

            username: document.getElementById("edit-username").value,
            email: document.getElementById("edit-email").value,
            phone: document.getElementById("edit-phone").value,
            full_name: document.getElementById("edit-full-name").value,
            birthday: document.getElementById("edit-birthday").value

        }

        const d = await api("/user/profile", "PATCH", payload)

        renderProfile(d)
        toggleEdit(false)

        setStatus("Đã cập nhật hồ sơ")

    } catch (e) {

        setStatus(e.message, true)

    }

}


/* =========================
UPLOAD AVATAR
========================= */

btnUploadAvatar.onclick = async () => {

    const f = avatarFile.files[0]
    if (!f) return

    const fd = new FormData()
    fd.append("avatar", f)

    const r = await fetch("/user/avatar/upload", {
        method: "POST",
        body: fd
    })

    const d = await r.json()

    avatarPreview.src = d.avatar

}


/* =========================
CHANGE PASSWORD
========================= */

btnChangePassword.onclick = async () => {

    try {

        await api("/user/password", "PATCH", {

            current_password: currentPassword.value,
            new_password: newPassword.value

        })

        setStatus("Đổi mật khẩu thành công")

    } catch (e) {

        setStatus(e.message, true)

    }

}


/* =========================
ORDER HISTORY
========================= */

btnLoadOrders.onclick = async () => {

    const d = await api("/user/purchase-history")

    const box = document.getElementById("orders-container")
    box.innerHTML = ""

    d.orders.forEach(o => {

        const div = document.createElement("div")
        div.className = "order-card"

        div.innerHTML = `
        <b>Đơn #${o.order_id}</b> - ${o.status}
        <br>
        Tổng tiền: ${o.total_price}
        `

        box.appendChild(div)

    })

}

/* =========================
FOLLOWING SHOPS
========================= */

function renderFollowingShops(items) {
    const box = document.getElementById("following-shops-container")
    if (!box) return

    if (!items || !items.length) {
        box.innerHTML = "<p>Bạn chưa theo dõi shop nào.</p>"
        return
    }

    box.innerHTML = items.map((item) => `
      <a class="address-card" href="${item.shop_url}" style="display:block;text-decoration:none;color:inherit;">
        <div class="address-text">
          <strong>${item.name || "Shop"}</strong><br>
          Nhấn để mở trang shop
        </div>
      </a>
    `).join("")
}

async function loadFollowingShops() {
    try {
        const data = await api("/user/following-shops")
        renderFollowingShops(data.items || [])
    } catch (e) {
        renderFollowingShops([])
    }
}

/* =========================
ADDRESS
========================= */

function resetAddress() {

    addrName.value = ""
    addrPhone.value = ""
    addrCity.value = ""
    addrDistrict.value = ""
    addrWard.value = ""
    addrLine.value = ""
    addrDefault.checked = false

}


/* DELETE ADDRESS */

async function deleteAddr(addressId) {

    if (!confirm("Xóa địa chỉ?")) return

    await api(`/user/address/${addressId}`, "DELETE")

    await loadProfile()

}


/* SET DEFAULT */

async function setDefault(addressId) {

    await api(`/user/address/${addressId}/default`, "POST")

    await loadProfile()

}


/* =========================
LOCATION API
========================= */

async function loadCities() {

    const data = await api("/user/api/provinces")
    console.log("[address] provinces", data)
    addrCity.innerHTML = `<option value="">Tỉnh / Thành phố</option>`

    data.forEach(c => {

        const opt = document.createElement("option")

        opt.value = String(c.code)
        opt.textContent = c.name

        addrCity.appendChild(opt)

    })

}


async function loadDistricts(city) {

    if (!city) {
        addrDistrict.innerHTML = `<option value="">Quận / Huyện</option>`
        addrWard.innerHTML = `<option value="">Phường / Xã</option>`
        return
    }

    const data2 = await api(`/user/api/districts?province_code=${encodeURIComponent(city)}`)
    console.log("[address] districts", data2)

    addrDistrict.innerHTML = `<option value="">Quận / Huyện</option>`

    data2.forEach(d => {

        const opt = document.createElement("option")

        opt.value = String(d.code)
        opt.textContent = d.name

        addrDistrict.appendChild(opt)

    })

}


async function loadWards(districtName) {

    if (!districtName) {
        addrWard.innerHTML = `<option value="">Phường / Xã</option>`
        return
    }

    const data2 = await api(`/user/api/wards?district_code=${encodeURIComponent(districtName)}`)
    console.log("[address] wards", data2)

    addrWard.innerHTML = `<option value="">Phường / Xã</option>`

    data2.forEach(w => {

        const opt = document.createElement("option")

        opt.value = w.code
        opt.textContent = w.name

        addrWard.appendChild(opt)

    })

}


/* EVENTS */
function bindAddressEvents() {

    if (btnAddAddress) {
        btnAddAddress.onclick = async () => {
            resetAddress()
            modal.classList.remove("hidden")

            try {
                await loadCities()
            } catch (e) {
                alert("Không tải được danh sách tỉnh/thành: " + e.message)
            }
        }
    }

    if (btnCloseAddress) {
        btnCloseAddress.onclick = () => {
            modal.classList.add("hidden")
        }
    }

}

if (btnSaveAddress) {

btnSaveAddress.onclick = async (e) => {

    e.stopPropagation()

    try {

        const cityText = addrCity.options[addrCity.selectedIndex]?.text || ""
        const districtText = addrDistrict.options[addrDistrict.selectedIndex]?.text || ""
        const wardText = addrWard.options[addrWard.selectedIndex]?.text || ""

        await api("/user/address", "POST", {
            full_name: addrName.value,
            phone: addrPhone.value,
            city: cityText,
            district: districtText,
            ward: wardText,
            address_line: addrLine.value,
            is_default: addrDefault.checked
        })

        modal.classList.add("hidden")
        await loadProfile()

    } catch (e) {

        alert("Lỗi khi lưu địa chỉ: " + e.message)

    }
}
}

/* =========================
INIT
========================= */

document.addEventListener("DOMContentLoaded", () => {

    loadProfile()
    loadFollowingShops()
    bindAddressEvents()

    /* THÊM ĐOẠN NÀY */

    addrCity.addEventListener("change", async () => {
        await loadDistricts(addrCity.value)
    })

    addrDistrict.addEventListener("change", async () => {
        await loadWards(addrDistrict.value)
    })

    /* ---------------- */

    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.add("hidden")
            }
        })
        const modalBox = document.querySelector(".modal-box")

        if (modalBox) {
            modalBox.addEventListener("click", (e) => {
                e.stopPropagation()
            })
        }

    }

})