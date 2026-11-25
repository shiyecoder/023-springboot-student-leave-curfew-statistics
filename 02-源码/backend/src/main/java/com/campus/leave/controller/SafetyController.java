package com.campus.leave.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.campus.leave.common.CurrentUser;
import com.campus.leave.common.R;
import com.campus.leave.entity.*;
import com.campus.leave.service.SafetyService;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/** 安全管理：晚归登记、返校码核验、未归核查工单、关怀记录 */
@RestController
@RequestMapping("/api")
public class SafetyController {

    private final SafetyService safetyService;

    public SafetyController(SafetyService safetyService) {
        this.safetyService = safetyService;
    }

    @GetMapping("/late/page")
    public R<IPage<LateReturn>> latePage(@RequestParam Map<String, String> params) {
        return R.ok(safetyService.latePage(params));
    }

    @PostMapping("/late")
    public R<LateReturn> addLate(@RequestBody Map<String, Object> body) {
        return R.ok(safetyService.addLate(body, CurrentUser.get()));
    }

    @GetMapping("/return/page")
    public R<IPage<ReturnRecord>> returnPage(@RequestParam Map<String, String> params) {
        return R.ok(safetyService.returnPage(params));
    }

    @PostMapping("/return/verify")
    public R<ReturnRecord> verify(@RequestBody Map<String, String> body) {
        return R.ok(safetyService.verifyCode(body.get("code"), CurrentUser.get()));
    }

    @PostMapping("/return/{id}/manual")
    public R<ReturnRecord> manual(@PathVariable Long id, @RequestBody Map<String, String> body) {
        return R.ok(safetyService.manualVerify(id, body.get("remark"), CurrentUser.get()));
    }

    @GetMapping("/case/page")
    public R<IPage<AbsenceCase>> casePage(@RequestParam Map<String, String> params) {
        return R.ok(safetyService.casePage(params));
    }

    @PostMapping("/case")
    public R<AbsenceCase> createCase(@RequestBody Map<String, Object> body) {
        return R.ok(safetyService.createCaseManual(body, CurrentUser.get()));
    }

    @PostMapping("/case/{id}/close")
    public R<AbsenceCase> closeCase(@PathVariable Long id, @RequestBody Map<String, String> body) {
        return R.ok(safetyService.closeCase(id, body.get("remark"), CurrentUser.get()));
    }

    @GetMapping("/care/page")
    public R<IPage<CareRecord>> carePage(@RequestParam Map<String, String> params) {
        return R.ok(safetyService.carePage(params));
    }

    @PostMapping("/care")
    public R<CareRecord> addCare(@RequestBody Map<String, Object> body) {
        return R.ok(safetyService.addCare(body, CurrentUser.get()));
    }

    @GetMapping("/student/options")
    public R<List<SysUser>> studentOptions(@RequestParam(required = false) String keyword) {
        return R.ok(safetyService.studentOptions(keyword));
    }
}
