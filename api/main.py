"""FastAPI application — inventory API + Web UI."""

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from api.database import init_db, get_db, SessionLocal
from api.models import Group, Host, User
from api.schemas import HostCreate, HostUpdate, GroupCreate, GroupUpdate
from api.auth import get_current_user, hash_password, verify_password

app = FastAPI(title="Ansible Dynamic Inventory")

app.mount("/static", StaticFiles(directory="api/static"), name="static")

templates = Jinja2Templates(directory="api/templates")


@app.on_event("startup")
def startup():
    init_db()
    _seed_default_user()


def _seed_default_user():
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(username="admin", password_hash=hash_password("admin")))
            db.commit()
    finally:
        db.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(name="login.html", request=request)


@app.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="session_id", value=user.username, httponly=True)
            return response
        return templates.TemplateResponse(
            name="login.html", request=request, context={"error": "Invalid credentials"}
        )
    finally:
        db.close()


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    return response


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        host_count = db.query(Host).count()
        group_count = db.query(Group).count()
        return templates.TemplateResponse(
            name="dashboard.html", request=request,
            context={"user": user, "host_count": host_count, "group_count": group_count},
        )
    finally:
        db.close()


# ── Hosts CRUD ────────────────────────────────────────────────────────────────

@app.get("/hosts", response_class=HTMLResponse)
def hosts_list(request: Request, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        hosts = db.query(Host).all()
        groups = db.query(Group).all()
        return templates.TemplateResponse(
            name="hosts.html", request=request,
            context={"user": user, "hosts": hosts, "groups": groups},
        )
    finally:
        db.close()


@app.get("/hosts/add", response_class=HTMLResponse)
def host_add_form(request: Request, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        groups = db.query(Group).all()
        return templates.TemplateResponse(
            name="host_form.html", request=request,
            context={"user": user, "groups": groups, "host": None},
        )
    finally:
        db.close()


@app.post("/hosts/add")
def host_add_submit(
    request: Request,
    name: str = Form(...),
    group_id: str = Form(""),
    host_ip: str = Form(""),
    host_user: str = Form(""),
    host_password: str = Form(""),
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        vars_dict = {}
        if host_ip:
            vars_dict["ansible_host"] = host_ip
        if host_user:
            vars_dict["ansible_user"] = host_user
        if host_password:
            vars_dict["ansible_password"] = host_password

        gid = int(group_id) if group_id else None
        host = Host(name=name, group_id=gid, vars=vars_dict)
        db.add(host)
        db.commit()
        return RedirectResponse(url="/hosts", status_code=303)
    finally:
        db.close()


@app.get("/hosts/{host_id}/edit", response_class=HTMLResponse)
def host_edit_form(host_id: int, request: Request, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        host = db.query(Host).filter(Host.id == host_id).first()
        if not host:
            raise HTTPException(status_code=404)
        groups = db.query(Group).all()
        return templates.TemplateResponse(
            name="host_form.html", request=request,
            context={"user": user, "groups": groups, "host": host},
        )
    finally:
        db.close()


@app.post("/hosts/{host_id}/edit")
def host_edit_submit(
    host_id: int,
    request: Request,
    name: str = Form(...),
    group_id: str = Form(""),
    host_ip: str = Form(""),
    host_user: str = Form(""),
    host_password: str = Form(""),
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        host = db.query(Host).filter(Host.id == host_id).first()
        if not host:
            raise HTTPException(status_code=404)

        vars_dict = {}
        if host_ip:
            vars_dict["ansible_host"] = host_ip
        if host_user:
            vars_dict["ansible_user"] = host_user
        if host_password:
            vars_dict["ansible_password"] = host_password

        host.name = name
        host.group_id = int(group_id) if group_id else None
        host.vars = vars_dict
        db.commit()
        return RedirectResponse(url="/hosts", status_code=303)
    finally:
        db.close()


@app.post("/hosts/{host_id}/delete")
def host_delete(host_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        host = db.query(Host).filter(Host.id == host_id).first()
        if host:
            db.delete(host)
            db.commit()
        return RedirectResponse(url="/hosts", status_code=303)
    finally:
        db.close()


# ── Groups CRUD ───────────────────────────────────────────────────────────────

@app.get("/groups", response_class=HTMLResponse)
def groups_list(request: Request, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        groups = db.query(Group).all()
        return templates.TemplateResponse(
            name="groups.html", request=request,
            context={"user": user, "groups": groups},
        )
    finally:
        db.close()


@app.get("/groups/add", response_class=HTMLResponse)
def group_add_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        name="group_form.html", request=request,
        context={"user": user, "group": None},
    )


@app.post("/groups/add")
def group_add_submit(
    request: Request,
    name: str = Form(...),
    ansible_become: str = Form(""),
    ansible_become_method: str = Form(""),
    ansible_ssh_private_key_file: str = Form(""),
    ansible_python_interpreter: str = Form(""),
    ansible_ssh_common_args: str = Form(""),
    ansible_connection: str = Form(""),
    ansible_port: str = Form(""),
    ansible_winrm_transport: str = Form(""),
    ansible_winrm_server_cert_validation: str = Form(""),
    ansible_password: str = Form(""),
    ansible_become_user: str = Form(""),
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        vars_dict = {}
        if ansible_become:
            vars_dict["ansible_become"] = ansible_become
        if ansible_become_method:
            vars_dict["ansible_become_method"] = ansible_become_method
        if ansible_ssh_private_key_file:
            vars_dict["ansible_ssh_private_key_file"] = ansible_ssh_private_key_file
        if ansible_python_interpreter:
            vars_dict["ansible_python_interpreter"] = ansible_python_interpreter
        if ansible_ssh_common_args:
            vars_dict["ansible_ssh_common_args"] = ansible_ssh_common_args
        if ansible_connection:
            vars_dict["ansible_connection"] = ansible_connection
        if ansible_port:
            vars_dict["ansible_port"] = int(ansible_port)
        if ansible_winrm_transport:
            vars_dict["ansible_winrm_transport"] = ansible_winrm_transport
        if ansible_winrm_server_cert_validation:
            vars_dict["ansible_winrm_server_cert_validation"] = ansible_winrm_server_cert_validation
        if ansible_password:
            vars_dict["ansible_password"] = ansible_password
        if ansible_become_user:
            vars_dict["ansible_become_user"] = ansible_become_user
        group = Group(name=name, vars=vars_dict)
        db.add(group)
        db.commit()
        return RedirectResponse(url="/groups", status_code=303)
    finally:
        db.close()


@app.get("/groups/{group_id}/edit", response_class=HTMLResponse)
def group_edit_form(group_id: int, request: Request, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404)
        return templates.TemplateResponse(
            name="group_form.html", request=request,
            context={"user": user, "group": group},
        )
    finally:
        db.close()


@app.post("/groups/{group_id}/edit")
def group_edit_submit(
    group_id: int,
    request: Request,
    name: str = Form(...),
    ansible_become: str = Form(""),
    ansible_become_method: str = Form(""),
    ansible_ssh_private_key_file: str = Form(""),
    ansible_python_interpreter: str = Form(""),
    ansible_ssh_common_args: str = Form(""),
    ansible_connection: str = Form(""),
    ansible_port: str = Form(""),
    ansible_winrm_transport: str = Form(""),
    ansible_winrm_server_cert_validation: str = Form(""),
    ansible_password: str = Form(""),
    ansible_become_user: str = Form(""),
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404)
        vars_dict = {}
        if ansible_become:
            vars_dict["ansible_become"] = ansible_become
        if ansible_become_method:
            vars_dict["ansible_become_method"] = ansible_become_method
        if ansible_ssh_private_key_file:
            vars_dict["ansible_ssh_private_key_file"] = ansible_ssh_private_key_file
        if ansible_python_interpreter:
            vars_dict["ansible_python_interpreter"] = ansible_python_interpreter
        if ansible_ssh_common_args:
            vars_dict["ansible_ssh_common_args"] = ansible_ssh_common_args
        if ansible_connection:
            vars_dict["ansible_connection"] = ansible_connection
        if ansible_port:
            vars_dict["ansible_port"] = int(ansible_port)
        if ansible_winrm_transport:
            vars_dict["ansible_winrm_transport"] = ansible_winrm_transport
        if ansible_winrm_server_cert_validation:
            vars_dict["ansible_winrm_server_cert_validation"] = ansible_winrm_server_cert_validation
        if ansible_password:
            vars_dict["ansible_password"] = ansible_password
        if ansible_become_user:
            vars_dict["ansible_become_user"] = ansible_become_user
        group.name = name
        group.vars = vars_dict
        db.commit()
        return RedirectResponse(url="/groups", status_code=303)
    finally:
        db.close()


@app.post("/groups/{group_id}/delete")
def group_delete(group_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            db.delete(group)
            db.commit()
        return RedirectResponse(url="/groups", status_code=303)
    finally:
        db.close()


# ── Ansible Inventory API (no auth) ──────────────────────────────────────────

@app.get("/api/hosts")
def api_hosts():
    db = SessionLocal()
    try:
        hosts = db.query(Host).all()
        groups = db.query(Group).all()
        group_vars_map = {g.name: g.vars or {} for g in groups}

        result = []
        for host in hosts:
            entry = {"name": host.name}

            if host.group_id:
                group = db.query(Group).filter(Group.id == host.group_id).first()
                if group:
                    entry["group_name"] = group.name
                    for k, v in (group.vars or {}).items():
                        if k not in (host.vars or {}):
                            entry[k] = v

            for k, v in (host.vars or {}).items():
                entry[k] = v

            result.append(entry)

        return JSONResponse(content=result)
    finally:
        db.close()


@app.get("/api/groups")
def api_groups():
    db = SessionLocal()
    try:
        groups = db.query(Group).all()
        result = [{"name": g.name, "vars": g.vars or {}} for g in groups]
        return JSONResponse(content=result)
    finally:
        db.close()
