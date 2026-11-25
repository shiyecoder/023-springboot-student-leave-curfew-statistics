package com.campus.leave.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.campus.leave.common.BizException;
import com.campus.leave.common.CurrentUser;
import com.campus.leave.common.R;
import com.campus.leave.config.JwtUtil;
import com.campus.leave.entity.*;
import com.campus.leave.mapper.*;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/** 认证与个人中心：登录、当前用户、动态菜单、改密、资料与头像 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final SysUserMapper userMapper;
    private final SysRoleMapper roleMapper;
    private final SysMenuMapper menuMapper;
    private final SysRoleMenuMapper roleMenuMapper;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder encoder;

    public AuthController(SysUserMapper userMapper, SysRoleMapper roleMapper, SysMenuMapper menuMapper,
                          SysRoleMenuMapper roleMenuMapper, JwtUtil jwtUtil, PasswordEncoder encoder) {
        this.userMapper = userMapper;
        this.roleMapper = roleMapper;
        this.menuMapper = menuMapper;
        this.roleMenuMapper = roleMenuMapper;
        this.jwtUtil = jwtUtil;
        this.encoder = encoder;
    }

    @PostMapping("/login")
    public R<Map<String, Object>> login(@RequestBody Map<String, String> body) {
        String username = body.getOrDefault("username", "").trim();
        String password = body.getOrDefault("password", "");
        if (username.isEmpty() || password.isEmpty()) {
            throw new BizException("请输入账号与密码");
        }
        SysUser user = userMapper.selectOne(new QueryWrapper<SysUser>().eq("username", username));
        if (user == null || !encoder.matches(password, user.getPassword())) {
            throw new BizException("账号或密码错误");
        }
        if (user.getStatus() == null || user.getStatus() != 1) {
            throw new BizException("账号已停用，请联系管理员");
        }
        user.setLastLogin(LocalDateTime.now());
        userMapper.updateById(user);
        user.setPassword(null);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("token", jwtUtil.generate(user.getId(), user.getUsername(), user.getRoleCode()));
        data.put("user", user);
        data.put("menus", menusOf(user.getRoleCode()));
        return R.ok(data);
    }

    @GetMapping("/me")
    public R<Map<String, Object>> me() {
        SysUser user = CurrentUser.get();
        user.setPassword(null);
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("user", user);
        data.put("menus", menusOf(user.getRoleCode()));
        data.put("role", roleMapper.selectOne(new QueryWrapper<SysRole>().eq("code", user.getRoleCode())));
        return R.ok(data);
    }

    /** 按角色动态下发菜单树（菜单权限与按钮权限分开返回） */
    @GetMapping("/menus")
    public R<List<Map<String, Object>>> menus() {
        return R.ok(menusOf(CurrentUser.role()));
    }

    @PostMapping("/password")
    public R<Void> changePassword(@RequestBody Map<String, String> body) {
        SysUser user = userMapper.selectById(CurrentUser.id());
        String oldPwd = body.getOrDefault("oldPassword", "");
        String newPwd = body.getOrDefault("newPassword", "");
        if (!encoder.matches(oldPwd, user.getPassword())) {
            throw new BizException("原密码不正确");
        }
        if (newPwd.length() < 6) {
            throw new BizException("新密码不少于 6 位");
        }
        user.setPassword(encoder.encode(newPwd));
        userMapper.updateById(user);
        return R.ok();
    }

    @PutMapping("/profile")
    public R<SysUser> updateProfile(@RequestBody SysUser body) {
        SysUser user = userMapper.selectById(CurrentUser.id());
        if (body.getRealName() != null) {
            user.setRealName(body.getRealName());
        }
        if (body.getPhone() != null) {
            user.setPhone(body.getPhone());
        }
        if (body.getGuardianName() != null) {
            user.setGuardianName(body.getGuardianName());
        }
        if (body.getGuardianPhone() != null) {
            user.setGuardianPhone(body.getGuardianPhone());
        }
        if (body.getAvatar() != null) {
            user.setAvatar(body.getAvatar());
        }
        userMapper.updateById(user);
        user.setPassword(null);
        return R.ok(user);
    }

    /** 菜单树：只取当前角色授权且 visible=1 的目录/菜单，按钮权限单独返回 */
    private List<Map<String, Object>> menusOf(String roleCode) {
        SysRole role = roleMapper.selectOne(new QueryWrapper<SysRole>().eq("code", roleCode));
        List<Long> ids = new ArrayList<>();
        if (role != null) {
            ids = roleMenuMapper.selectList(new QueryWrapper<SysRoleMenu>().eq("role_id", role.getId()))
                    .stream().map(SysRoleMenu::getMenuId).collect(Collectors.toList());
        }
        if (ids.isEmpty()) {
            return List.of();
        }
        List<SysMenu> all = menuMapper.selectList(new QueryWrapper<SysMenu>().in("id", ids).orderByAsc("sort"));
        List<SysMenu> roots = all.stream()
                .filter(m -> (m.getParentId() == null || m.getParentId() == 0) && !"BUTTON".equals(m.getType()))
                .sorted(Comparator.comparing(SysMenu::getSort))
                .collect(Collectors.toList());
        List<Map<String, Object>> tree = new ArrayList<>();
        for (SysMenu root : roots) {
            Map<String, Object> node = toNode(root);
            if ("DIR".equals(root.getType())) {
                List<Map<String, Object>> children = all.stream()
                        .filter(m -> Objects.equals(m.getParentId(), root.getId()) && !"BUTTON".equals(m.getType()))
                        .sorted(Comparator.comparing(SysMenu::getSort))
                        .map(this::toNode).collect(Collectors.toList());
                node.put("children", children);
            }
            tree.add(node);
        }
        return tree;
    }

    private Map<String, Object> toNode(SysMenu m) {
        Map<String, Object> n = new LinkedHashMap<>();
        n.put("id", m.getId());
        n.put("name", m.getName());
        n.put("path", m.getPath());
        n.put("component", m.getComponent());
        n.put("icon", m.getIcon());
        n.put("perm", m.getPerm());
        n.put("type", m.getType());
        return n;
    }
}
