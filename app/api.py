import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Body, Form, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from app.Utils.logger import log
from app.dao import UserDao, RoleDao, ManagerDao, RoomDao, ApproveDao, PhoDao
from app.entity.SysManager import SysManager
from app.entity.SysRoom import SysRoom
from app.entity.SysUser import SysUser

# 创建FastAPI应用
app = FastAPI()

app.mount("/app/static", StaticFiles(directory="app/static"), name="static")

logger = log()
"""
设置CORS
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 允许的 HTTP 方法
    allow_headers=["*"],  # 允许所有标头
)
# 定义密钥和算法
SECRET_KEY = "CMCCMY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60
# 初始密码
INIT_PASSWORD = "password"

# 照片文件夹
PHOTO_DIR = "app/static/photos"

# OAuth2PasswordBearer会创建一个依赖项来验证令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class PhotoResponse(BaseModel):
    path: str
    type: str


class PhotographResponse(BaseModel):
    photos: List[PhotoResponse]


# 扩展 OAuth2PasswordRequestForm，使其支持 telephone 字段
class ExtendedOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    def __init__(self, username: str = Form(...), password: str = Form(None), telephone: str = Form(...)):
        super().__init__(username=username, password=password)
        self.password = password
        self.telephone = telephone


# 验证用户是否有效
def authenticate_user(username: str, password: str, telephone: str):
    user = SysUser(username=username, password=password, telephone=telephone)
    sys_user = UserDao.getUserByName(username, telephone)
    if not sys_user:
        return False, f"用户不存在"
    role = RoleDao.get_role_by_user(sys_user.id)
    if not role:
        return False, f"用户权限不存在"
    # 如果是施工队
    if role[0].id == 3:
        return True, user
    if UserDao.login(user)[0]:
        return True, user
    else:
        return False, f"用户检验失败"


# 生成访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 登录并获取Token的路由
@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: ExtendedOAuth2PasswordRequestForm = Depends()):
    res = authenticate_user(form_data.username, form_data.password, form_data.telephone)
    if not res[0]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=res[1],
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = res[1]
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "username": user.username,
            "password": user.password,
            "telephone": user.telephone
        }, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 依赖项，通过Token获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        password: str = payload.get("password")
        telephone: str = payload.get("telephone")
        if username is None or telephone is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = SysUser(username=username, password=password, telephone=telephone)
    sys_user = UserDao.getUserByName(username, telephone)
    if not sys_user:
        raise credentials_exception
    role = RoleDao.get_role_by_user(sys_user.id)
    if role:
        if role[0].id == 3:
            return sys_user
    if UserDao.login(user)[0]:
        sys_user = UserDao.getUserByPassword(user)
        return sys_user
    else:
        raise credentials_exception


# 受保护的路由
@app.get("/users/me")
async def read_users_me(current_user: SysUser = Depends(get_current_user)):
    return current_user

@app.get("/users/select")
async def select_user(params: str, current_user: SysUser = Depends(get_current_user)):
    # 判断参数是用户名还是手机号
    if params.isdigit():
        res = UserDao.selectUserByTelephone(params)
    else:
        res = UserDao.selectUserByName(params)
    if res[0]:
        return {"detail": res[1]}
    raise HTTPException(status_code=404, detail="User not found")



# 管理员获取用户信息
@app.get("/users/list", response_model=dict)
async def user_list(page: int = 1, current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    else:
        res = UserDao.user_list(page)
        if res[0]:
            return {
                "total_pages": res[2],
                "users": res[3]
            }
        return {
            "details": res[1],
            "total_pages": res[2],
            "users": res[3]
        }


# 修改用户信息
@app.post("/users/change", response_model=dict)
async def change(telephone: str = Body(required=True),
                 current_user: SysUser = Depends(get_current_user)):
    sys_user = SysUser(id=current_user.id, username=current_user.username,
                       password=current_user.password, telephone=current_user.telephone)
    res = UserDao.user_change(sys_user, telephone)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/users/change，用户信息修改失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 修改密码
@app.post("/users/change/password", response_model=dict)
async def change_password(password: str = Body(required=True),
                          current_user: SysUser = Depends(get_current_user)):
    sys_user = SysUser(id=current_user.id, username=current_user.username,
                       password=current_user.password, telephone=current_user.telephone)
    res = UserDao.change_password(sys_user, password)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/users/change/password，密码修改失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 管理员重置用户密码
@app.post("/users/reset/password", response_model=dict)
async def reset_password(username: str = Body(required=True),
                         telephone: str = Body(required=True),
                         current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    else:
        target_user = SysUser(username=username, telephone=telephone)
        res = UserDao.change_password(target_user, INIT_PASSWORD)
        if res[0]:
            logger.info(f"{target_user.username}密码重置为{INIT_PASSWORD}")
            return {"detail": res[1]}
        else:
            logger.error(f"接口:/users/reset/password，密码重置失败，失败原因：{res[1]}")
            raise HTTPException(status_code=403, detail=res[1])


# 新建用户
@app.post("/users/create", response_model=dict)
async def create_user(username: str = Body(required=True), password: str = Body(required=True),
                      telephone: str = Body(required=True)):
    sys_user = SysUser(username=username, password=password, telephone=telephone)
    res = UserDao.create_user(sys_user)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/users/create，用户创建失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 用户删除
@app.delete("/users/delete", response_model=dict)
async def delete_user(username: str,
                      telephone: str,
                      current_user: SysUser = Depends(get_current_user)):
    target_id = UserDao.getUserIdByName(username, telephone)
    if target_id is None:
        raise HTTPException(status_code=403, detail="User not found")
    res = UserDao.user_delete(current_user, target_id)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/users/delete，用户删除失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 获取用户角色
@app.get("/users/me/role", response_model=dict)
async def read_users_role(current_user: SysUser = Depends(get_current_user)):
    role = RoleDao.get_role_by_user(current_user.id)[0]
    if role is None:
        raise HTTPException(status_code=403, detail="Role not found")
    else:
        role_dict = {"id": role.id, "name": role.name}
        return role_dict


# 管理员获得用户角色
@app.get("/users/role/get", response_model=dict)
async def get_role(username: str = Body(required=True),
                   telephone: str = Body(required=True),
                   current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)[0]
    if role_id.id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    target_user = UserDao.getUserByName(username, telephone)
    role = RoleDao.get_role_by_user(target_user.id)
    if role is None:
        raise HTTPException(status_code=403, detail="Role not found")
    else:
        role_dict = {
            "username": target_user.username,
            "telephone": target_user.telephone,
            "id": role[0].id,
            "name": role[0].name
        }
        return role_dict


# 用户角色修改
@app.post("/users/change/role", response_model=dict)
async def change_role(username: str = Body(required=True),
                      telephone: str = Body(required=True),
                      role_id: int = Body(required=True),
                      current_user: SysUser = Depends(get_current_user)):
    target_id = UserDao.getUserIdByName(username, telephone)
    res = RoleDao.role_change(current_user, target_id, role_id)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/users/change/role，用户角色修改失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])

@app.get("/manager/select")
async def select_manager(params: str, current_user: SysUser = Depends(get_current_user)):
    if params.isdigit():
        res = ManagerDao.selectManagerByTelephone(params)
    else:
        res = ManagerDao.selectManagerByName(params)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/manager/select，获取用户信息失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 机房长信息
@app.get("/manager/me")
async def manager_me(current_user: SysUser = Depends(get_current_user)):
    res = ManagerDao.get_manager(current_user)
    if res[0]:
        return res[1]
    else:
        logger.error(f"接口:/manager/me，获取用户信息失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 查询指定机房长信息
@app.get("/manager/get")
async def get_manager(username: str = Body(required=True),
                      telephone: str = Body(required=True),
                      current_user: SysUser = Depends(get_current_user)):
    target_user = UserDao.getUserByName(username, telephone)
    res = ManagerDao.get_manager(target_user)
    if res[0]:
        return res[1]
    else:
        logger.error(f"接口:/manager/get，获取用户信息失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 查询机房长列表
@app.get("/manager/list", response_model=dict)
async def get_manager_list(page: int = 1, current_user: SysUser = Depends(get_current_user)):
    res = ManagerDao.get_manager_list(page)
    if res[0]:
        return {
            "total_pages": res[2],
            "managers": res[3]
        }
    return {
        "details": res[1],
        "total_pages": res[2],
        "managers": res[3]
    }


# 新增机房长
@app.post("/manager/create", response_model=dict)
async def create_manager(username: str = Body(required=True),
                         telephone: str = Body(required=True),
                         address: str = '',
                         current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    sys_user = UserDao.getUserIdByName(username, telephone)
    sys_manager = SysManager(user_id=sys_user.id, address=address, telephone=telephone)
    res = ManagerDao.create_manager(sys_manager)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/manager/create，用户创建失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 删除机房长
@app.delete("/manager/delete", response_model=dict)
async def delete_manager(username: str,
                         telephone: str,
                         current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    target_id = UserDao.getUserIdByName(username, telephone)
    res = ManagerDao.delete_manager(target_id)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/manager/delete，用户删除失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 修改机房长信息
@app.post("/manager/change", response_model=dict)
async def change_manager(address: str = Body(required=True),
                         current_user: SysUser = Depends(get_current_user)):
    res = ManagerDao.user_change(current_user, address)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/manager/change，用户信息修改失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 管理员修改机房长信息
@app.post("/manager/admin/change", response_model=dict)
async def admin_change_manager(username: str = Body(required=True),
                               telephone: str = Body(required=True),
                               address: str = Body(required=True),
                               current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    target_user = UserDao.getUserIdByName(username, telephone)
    res = ManagerDao.user_change(target_user, address)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/manager/admin/change/，用户信息修改失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 机房信息列表查询
@app.get("/room/list", response_model=dict)
async def get_room_list(page: int = 1, current_user: SysUser = Depends(get_current_user)):
    res = RoomDao.get_room_list(page)
    if res[0]:
        return {
            "total_pages": res[2],
            "rooms": res[3]
        }
    return {
        "details": res[1],
        "total_pages": res[2],
        "rooms": res[3]
    }


# 查询指定机房信息
@app.get("/room/get")
async def get_room(name: str, current_user: SysUser = Depends(get_current_user)):
    res = RoomDao.get_room_by_name(name)
    if res[0]:
        return res[1]
    else:
        logger.error(f"接口:/room/get，获取用户信息失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 查询指定机房信息
@app.get("/room/get/id")
async def get_room_by_id(room_id: int, current_user: SysUser = Depends(get_current_user)):
    res = RoomDao.get_room_by_id(room_id)
    if res[0]:
        return res[1]
    else:
        logger.error(f"接口:/room/get/id，获取用户信息失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 管理员增加机房
@app.post("/room/create", response_model=dict)
async def create_room(name: str = Body(required=True),
                      address: str = Body(required=True),
                      manager_id: int = Body(required=True),
                      room_type: str = Body(required=True),
                      status: str = Body(required=True),
                      sys_name: str = Body(required=True),
                      current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    sys_room = SysRoom(name=name, address=address, manager_id=manager_id,
                       room_type=room_type, status=status, sys_name=sys_name)
    res = RoomDao.create_room(sys_room)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/room/create，创建机房失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 管理员删除机房
@app.delete("/room/delete", response_model=dict)
async def delete_room(name: str,
                      current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        logger.info(f"接口:/room/delete，删除机房失败，失败原因：No permission")
        raise HTTPException(status_code=403, detail="No permission")
    res = RoomDao.delete_room_by_name(name)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/room/delete，删除机房失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


@app.delete("/room/delete/id", response_model=dict)
async def delete_room_by_id(room_id: int,
                            current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 1:
        logger.info(f"接口:/room/delete/id，删除机房失败，失败原因：No permission")
        raise HTTPException(status_code=403, detail="No permission")
    res = RoomDao.delete_room_by_id(room_id)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/room/delete/id，删除机房失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 管理员和机房长修改机房信息
@app.post("/room/change", response_model=dict)
async def change_room(name: str = Body(required=True),
                      address: str = Body(required=True),
                      manager_id: int = Body(required=True),
                      room_type: str = Body(required=True),
                      status: str = Body(required=True),
                      sys_name: str = Body(required=True),
                      current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    user = ManagerDao.get_user_by_id(manager_id)
    if role_id[0].id != 1 and user.id != current_user.id:
        raise HTTPException(status_code=403, detail="No permission")
    sys_room = SysRoom(name=name, address=address, manager_id=manager_id,
                       room_type=room_type, status=status, sys_name=sys_name)
    res = RoomDao.change_room(sys_room)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/room/change，修改机房失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 发起机房开门请求
@app.post("/approve/open", response_model=dict)
async def approve_open(room_id: int = Body(required=True),
                       notes: Optional[str] = Body(None),
                       current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)
    if role_id[0].id != 3:
        res = ApproveDao.direct_open(current_user, room_id, notes)
        if res[0]:
            return {"detail": res[1]}
        else:
            logger.error(f"接口:/approve/open，直接开门失败，失败原因：{res[1]}")
            raise HTTPException(status_code=403, detail=res[1])
    res = ApproveDao.approve_open(current_user, room_id, notes)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/approve/open，申请开门失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 获得审批工单
@app.get("/approve/list", response_model=dict)
async def get_approve_list(pro_status: Optional[bool] = None,
                           page: int = 1,
                           current_user: SysUser = Depends(get_current_user)):
    res = ApproveDao.get_approve_list(page, pro_status, current_user)
    if res[0]:
        return {
            "total_pages": res[2],
            "approves": res[3]
        }
    else:
        logger.error(f"接口:/approve/list，获取工单列表失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 获得自己发起的审批工单
@app.get("/approve/me", response_model=dict)
async def get_approve_list(pro_status: Optional[bool] = None,
                           page: int = 1,
                           current_user: SysUser = Depends(get_current_user)):
    res = ApproveDao.get_approve_me(page, pro_status, current_user)
    if res[0]:
        return {
            "total_pages": res[2],
            "approves": res[3]
        }
    else:
        logger.error(f"接口:/approve/me，获取工单列表失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 审批开门请求
@app.post("/approve/approve", response_model=dict)
async def approve_approve(approve_id: int = Body(required=True),
                          approve_status: bool = Body(required=True),
                          current_user: SysUser = Depends(get_current_user)):
    res = ApproveDao.approve_approve(approve_id, approve_status, current_user)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/approve/approve，审批工单失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 管理员删除审批工单
@app.delete("/approve/delete", response_model=dict)
async def delete_approve(approve_id: int,
                         current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)[0].id
    if role_id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    res = ApproveDao.delete_approve(approve_id)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/approve/delete，删除工单失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 进入机房上传照片
@app.post("/open/photograph/in", response_model=dict)
async def open_photograph_in(
        file: UploadFile = File(...),
        approve_id: int = Form(...),
        current_user: SysUser = Depends(get_current_user)):
    # 如果不存在上传目录，则创建它
    if not os.path.exists(PHOTO_DIR):
        os.makedirs(PHOTO_DIR)
    # 文件唯一UUID
    filename = f"{uuid.uuid4()}_{file.filename}"

    # 构建文件保存路径
    file_location = os.path.join(PHOTO_DIR, filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    app_type = "in"
    res = PhoDao.save_pho(file_location, approve_id, app_type)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/open/photograph/in，保存照片失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 开门
@app.post("/open", response_model=dict)
async def open_room(approve_id: int,
                    current_user: SysUser = Depends(get_current_user)):
    res = ApproveDao.open_room(approve_id, current_user)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/open，开门失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 出机房照片
@app.post("/open/photograph/out", response_model=dict)
async def open_photograph_out(
        file: UploadFile = File(...),
        approve_id: int = Form(...),
        current_user: SysUser = Depends(get_current_user)):
    # 如果不存在上传目录，则创建它
    if not os.path.exists(PHOTO_DIR):
        os.makedirs(PHOTO_DIR)
    # 文件唯一UUID
    filename = f"{uuid.uuid4()}_{file.filename}"
    # 构建文件保存路径
    file_location = os.path.join(PHOTO_DIR, filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    app_type = "out"
    res = PhoDao.save_pho(file_location, approve_id, app_type)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/open/photograph/out，保存照片失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 关门
@app.post("/close", response_model=dict)
async def close_room(
        approve_id: int,
        current_user: SysUser = Depends(get_current_user)):
    res = ApproveDao.close_room(approve_id, current_user)
    if res[0]:
        return {"detail": res[1]}
    else:
        logger.error(f"接口:/close，关门失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 获得异常工单
@app.get("/approve/error/me", response_model=dict)
async def get_approve_error_me(
        page: int = 1,
        current_user: SysUser = Depends(get_current_user)):
    res = ApproveDao.get_approve_error_me(current_user, page)
    if res[0]:
        return {
            "total_pages": res[1],
            "approves": res[2]
        }
    else:
        logger.error(f"接口:/approve/error/me，获取工单列表失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 超级用户获得异常工单
@app.get("/approve/error/list", response_model=dict)
async def get_approve_error_list(
        page: int = 1,
        current_user: SysUser = Depends(get_current_user)):
    role_id = RoleDao.get_role_by_user(current_user.id)[0].id
    if role_id != 1:
        raise HTTPException(status_code=403, detail="No permission")
    res = ApproveDao.get_approve_error_list(current_user, page)
    if res[0]:
        return {
            "total_pages": res[1],
            "approves": res[2]
        }
    else:
        logger.error(f"接口:/approve/error/list，获取工单列表失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


# 获得照片
@app.get("/approve/photograph", response_model=PhotographResponse)
async def get_photograph(approve_id: int, current_user: SysUser = Depends(get_current_user)):
    res = PhoDao.get_photograph(approve_id)
    if res[0]:
        photos_dict = res[1]
        return {"photos": photos_dict}

    else:
        logger.error(f"接口:/approve/photograph，获取照片失败，失败原因：{res[1]}")
        raise HTTPException(status_code=403, detail=res[1])


@app.get("/index")
async def index(current_user: SysUser = Depends(get_current_user)):
    return "hello world"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="100.107.207.44", port=8081, reload=False)
