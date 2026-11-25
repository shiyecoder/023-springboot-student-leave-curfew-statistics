package com.campus.leave.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.campus.leave.common.BizException;
import com.campus.leave.common.CurrentUser;
import com.campus.leave.common.R;
import com.campus.leave.entity.*;
import com.campus.leave.mapper.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/** 系统管理：用户、角色、菜单、字典、消息、文件上传 */
@RestController
@RequestMapping("/api")
public class SystemController {

    private final SysUserMapper userMapper;
    private final SysRoleMapper roleMapper;
    private final SysMenuMapper menuMapper;
    private final SysRoleMenuMapper roleMenuMapper;
    private final SysDictMapper dictMapper;
    private final SysMessageMapper messageMapper;
    private final SysFileMapper fileMapper;
    private final PasswordEncoder encoder;

    @Value("${app.upload.dir}")
    private String uploadDir;

    public SystemController(SysUserMapper userMapper, SysRoleMapper roleMapper, SysMenuMapper menuMapper,
                            SysRoleMenuMapper roleMenuMapper, SysDictMapper dictMapper, SysMessageMapper messageMapper,
                            SysFileMapper fileMapper, PasswordEncoder encoder) {
        this.userMapper = userMapper;
        this.roleMapper = roleMapper;
        this.menuMapper = menuMapper;
        this.roleMenuMapper = roleMenuMapper;
        this.dictMapper = dictMapper;
        this.messageMapper = messageMapper;
        this.fileMapper = fileMapper;
        this.encoder = encoder;
    }

    @GetMapping("/health")
    public R<String> health() {
        return R.ok("ok");
    }

    // ---------------- 用户 ----------------

    @GetMapping("/user/page")
    public R<IPage<SysUser>> userPage(@RequestParam Map<String, String> p) {
        QueryWrapper<SysUser> qw = new QueryWrapper<>();
        if (p.get("keyword") != null && !p.get("keyword").isBlank()) {
            qw.and(w -> w.like("real_name", p.get("keyword")).or().like("username", p.get("keyword")));
        }
        if (p.get("roleCode") != null && !p.get("roleCode").isBlank()) {
            qw.eq("role_code", p.get("roleCode"));
        }
        if (p.get("deptId") != null && !p.get("deptId").isBlank()) {
            qw.eq("dept_id", p.get("deptId"));
        }
        if (p.get("status") != null && !p.get("status").isBlank()) {
            qw.eq("status", p.get("status"));
        }
        qw.orderByAsc("id");
        int pageNo = p.get("page") == null ? 1 : Integer.parseInt(p.get("page"));
        int size = p.get("size") == null ? 10 : Integer.parseInt(p.get("size"));
        IPage<SysUser> page = userMapper.selectPage(new Page<>(pageNo, size), qw);
        page.getRecords().forEach(u -> u.setPassword(null));
        return R.ok(page);
    }

    @PostMapping("/user")
    public R<SysUser> createUser(@RequestBody SysUser user) {
        if (user.getUsername() == null || user.getUsername().isBlank()) {
            throw new BizException("账号不能为空");
        }
        user.setPassword(encoder.encode(user.getPassword() == null ? "123456" : user.getPassword()));
        user.setStatus(user.getStatus() == null ? 1 : user.getStatus());
        userMapper.insert(user);
        return R.ok(user);
    }

    @PutMapping("/user/{id}")
    public R<SysUser> updateUser(@PathVariable Long id, @RequestBody SysUser user) {
        SysUser db = userMapper.selectById(id);
        if (db == null) {
            throw new BizException("用户不存在");
        }
        db.setRealName(user.getRealName());
        db.setPhone(user.getPhone());
        db.setRoleCode(user.getRoleCode());
        db.setDeptId(user.getDeptId());
        db.setDeptName(user.getDeptName());
        db.setClassName(user.getClassName());
        db.setStatus(user.getStatus());
        userMapper.updateById(db);
        db.setPassword(null);
        return R.ok(db);
    }

    @PostMapping("/user/{id}/reset")
    public R<Void> resetPassword(@PathVariable Long id) {
        SysUser db = userMapper.selectById(id);
        if (db == null) {
            throw new BizException("用户不存在");
        }
        db.setPassword(encoder.encode("123456"));
        userMapper.updateById(db);
        return R.ok();
    }

    @DeleteMapping("/user/{id}")
    public R<Void> deleteUser(@PathVariable Long id) {
        if (id == 1L) {
            throw new BizException("内置管理员不可删除");
        }
        userMapper.deleteById(id);
        return R.ok();
    }

    // ---------------- 角色与菜单 ----------------

    @GetMapping("/role/list")
    public R<List<Map<String, Object>>> roleList() {
        List<Map<String, Object>> list = new ArrayList<>();
        for (SysRole r : roleMapper.selectList(new QueryWrapper<SysRole>().orderByAsc("id"))) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", r.getId());
            m.put("code", r.getCode());
            m.put("name", r.getName());
            m.put("dataScope", r.getDataScope());
            m.put("remark", r.getRemark());
            m.put("userCount", userMapper.selectCount(new QueryWrapper<SysUser>().eq("role_code", r.getCode())));
            list.add(m);
        }
        return R.ok(list);
    }

    @GetMapping("/role/{id}/menus")
    public R<List<Long>> roleMenus(@PathVariable Long id) {
        List<Long> ids = new ArrayList<>();
        roleMenuMapper.selectList(new QueryWrapper<SysRoleMenu>().eq("role_id", id))
                .forEach(rm -> ids.add(rm.getMenuId()));
        return R.ok(ids);
    }

    @PostMapping("/role/{id}/menus")
    public R<Void> assignMenus(@PathVariable Long id, @RequestBody List<Long> menuIds) {
        roleMenuMapper.delete(new QueryWrapper<SysRoleMenu>().eq("role_id", id));
        for (Long mid : menuIds) {
            SysRoleMenu rm = new SysRoleMenu();
            rm.setRoleId(id);
            rm.setMenuId(mid);
            roleMenuMapper.insert(rm);
        }
        return R.ok();
    }

    /** 菜单管理：树形返回；菜单管理选项本身不参与角色分配（需求要求隐藏） */
    @GetMapping("/menu/tree")
    public R<List<Map<String, Object>>> menuTree() {
        List<SysMenu> all = menuMapper.selectList(new QueryWrapper<SysMenu>().orderByAsc("sort"));
        List<Map<String, Object>> roots = new ArrayList<>();
        for (SysMenu m : all) {
            if (m.getParentId() == null || m.getParentId() == 0) {
                Map<String, Object> node = node(m);
                List<Map<String, Object>> children = new ArrayList<>();
                for (SysMenu c : all) {
                    if (Objects.equals(c.getParentId(), m.getId())) {
                        children.add(node(c));
                    }
                }
                node.put("children", children);
                roots.add(node);
            }
        }
        return R.ok(roots);
    }

    @PostMapping("/menu")
    public R<SysMenu> saveMenu(@RequestBody SysMenu menu) {
        if (menu.getId() == null) {
            menuMapper.insert(menu);
        } else {
            menuMapper.updateById(menu);
        }
        return R.ok(menu);
    }

    @DeleteMapping("/menu/{id}")
    public R<Void> deleteMenu(@PathVariable Long id) {
        if (id <= 22) {
            throw new BizException("内置菜单不可删除，请先停用");
        }
        menuMapper.deleteById(id);
        return R.ok();
    }

    private Map<String, Object> node(SysMenu m) {
        Map<String, Object> n = new LinkedHashMap<>();
        n.put("id", m.getId());
        n.put("parentId", m.getParentId());
        n.put("name", m.getName());
        n.put("path", m.getPath());
        n.put("component", m.getComponent());
        n.put("perm", m.getPerm());
        n.put("type", m.getType());
        n.put("sort", m.getSort());
        n.put("visible", m.getVisible());
        return n;
    }

    // ---------------- 字典 / 消息 ----------------

    @GetMapping("/dict/{type}")
    public R<List<SysDict>> dict(@PathVariable String type) {
        return R.ok(dictMapper.selectList(new QueryWrapper<SysDict>().eq("dict_type", type).orderByAsc("sort")));
    }

    @GetMapping("/message/page")
    public R<IPage<SysMessage>> messages(@RequestParam(defaultValue = "1") int page,
                                         @RequestParam(defaultValue = "10") int size) {
        return R.ok(messageMapper.selectPage(new Page<>(page, size), new QueryWrapper<SysMessage>()
                .eq("receiver_id", CurrentUser.id()).orderByDesc("create_time")));
    }

    @PostMapping("/message/{id}/read")
    public R<Void> read(@PathVariable Long id) {
        SysMessage m = messageMapper.selectById(id);
        if (m != null) {
            m.setIsRead(1);
            messageMapper.updateById(m);
        }
        return R.ok();
    }

    // ---------------- 上传 ----------------

    /** 文件上传：保存到项目根 uploads/yyyyMM/，数据库存相对路径（禁止外链） */
    @PostMapping("/upload")
    public R<Map<String, Object>> upload(@RequestParam("file") MultipartFile file,
                                         @RequestParam(required = false, defaultValue = "PROOF") String bizType) throws IOException {
        if (file == null || file.isEmpty()) {
            throw new BizException("请选择要上传的文件");
        }
        String original = file.getOriginalFilename() == null ? "file" : file.getOriginalFilename();
        String ext = original.contains(".") ? original.substring(original.lastIndexOf('.') + 1).toLowerCase() : "";
        if (!List.of("jpg", "jpeg", "png", "pdf").contains(ext)) {
            throw new BizException("仅支持 JPG / PNG / PDF 文件");
        }
        if (file.getSize() > 10 * 1024 * 1024) {
            throw new BizException("单个文件不能超过 10MB");
        }
        String folder = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMM"));
        Path dir = Paths.get(uploadDir, folder).toAbsolutePath().normalize();
        Files.createDirectories(dir);
        String name = UUID.randomUUID().toString().replace("-", "") + "." + ext;
        Path target = dir.resolve(name);
        file.transferTo(target.toFile());

        String relative = "/uploads/" + folder + "/" + name;
        SysFile f = new SysFile();
        f.setFileName(original);
        f.setPath(relative);
        f.setSize(file.getSize());
        f.setContentType(file.getContentType());
        f.setBizType(bizType);
        f.setUploaderId(CurrentUser.id());
        fileMapper.insert(f);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("path", relative);
        data.put("fileName", original);
        data.put("size", file.getSize());
        return R.ok(data);
    }
}
