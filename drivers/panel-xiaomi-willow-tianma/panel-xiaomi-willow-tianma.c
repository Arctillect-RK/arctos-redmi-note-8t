// SPDX-License-Identifier: GPL-2.0-only
/*
 * Tianma NT36672A 1080x2340 video-mode panel of the Xiaomi Redmi Note 8T (willow)
 * and Redmi Note 8 (ginkgo).
 *
 * Timings and init sequence from downstream dsi-panel-nt36672a-tianma-fhd-video.dtsi.
 *
 * The panel is an in-cell TDDI: the NT36672A touch controller shares reset and
 * analog rails with the display. Toggling the reset GPIO or sending sleep-in (0x10)
 * kills the touch firmware that nt36xxx downloaded at boot, so this driver:
 *  - takes over the panel the bootloader already lit (no reset on first enable),
 *  - blanks with display-off (0x28) + brightness 0 and unblanks with 0x29,
 *  - never powers the rails down.
 * Backlight is DCS-controlled (downstream bl_ctrl_dcs): one 8-bit 0x51 byte.
 */

#include <linux/backlight.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/of.h>

#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>
#include <drm/drm_probe_helper.h>

#include <video/mipi_display.h>

#define WILLOW_BL_MAX	255
#define WILLOW_BL_DEF	184

struct willow_panel {
	struct drm_panel panel;
	struct mipi_dsi_device *dsi;
	struct gpio_desc *reset_gpio;
	bool inited;
};

static inline struct willow_panel *to_willow_panel(struct drm_panel *panel)
{
	return container_of(panel, struct willow_panel, panel);
}

static int willow_panel_init(struct willow_panel *ctx)
{
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	ctx->dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x25);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x18, 0x96);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x05, 0x04);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x20);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x78, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x24);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x82, 0x13);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x84, 0x31);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x88, 0x13);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x8a, 0x31);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x8e, 0xe4);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x8f, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x90, 0x80);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x26);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfb, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xa9, 0x12);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xaa, 0x10);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xae, 0x8a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xff, 0x10);
	mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 80);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x01);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x35, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x68, 0x04, 0x03);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x53, 0x2c);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x55, 0x00);
	mipi_dsi_dcs_set_display_on_multi(&dsi_ctx);

	ctx->dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

	return dsi_ctx.accum_err;
}

static int willow_panel_enable(struct drm_panel *panel)
{
	struct willow_panel *ctx = to_willow_panel(panel);
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };
	int ret;

	if (!ctx->inited) {
		/* First enable: panel is already on from the bootloader; re-send init, no reset. */
		ret = willow_panel_init(ctx);
		if (ret)
			dev_err(panel->dev, "init sequence failed: %d\n", ret);
		else
			dev_info(panel->dev, "panel init complete\n");
		ctx->inited = true;
		return ret;
	}

	mipi_dsi_dcs_set_display_on_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 20);

	return dsi_ctx.accum_err;
}

static int willow_panel_disable(struct drm_panel *panel)
{
	struct willow_panel *ctx = to_willow_panel(panel);
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	/* 0x28 only: 0x10 / reset would also kill the in-cell touch controller. */
	mipi_dsi_dcs_set_display_off_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 20);

	return dsi_ctx.accum_err;
}

static const struct drm_display_mode willow_mode = {
	.clock = (1080 + 90 + 2 + 120) * (2340 + 10 + 3 + 8) * 60 / 1000,
	.hdisplay = 1080,
	.hsync_start = 1080 + 90,
	.hsync_end = 1080 + 90 + 2,
	.htotal = 1080 + 90 + 2 + 120,
	.vdisplay = 2340,
	.vsync_start = 2340 + 10,
	.vsync_end = 2340 + 10 + 3,
	.vtotal = 2340 + 10 + 3 + 8,
	.width_mm = 67,
	.height_mm = 145,
	.type = DRM_MODE_TYPE_DRIVER,
};

static int willow_panel_get_modes(struct drm_panel *panel,
				  struct drm_connector *connector)
{
	return drm_connector_helper_get_modes_fixed(connector, &willow_mode);
}

static const struct drm_panel_funcs willow_panel_funcs = {
	.enable = willow_panel_enable,
	.disable = willow_panel_disable,
	.get_modes = willow_panel_get_modes,
};

static int willow_bl_update_status(struct backlight_device *bl)
{
	struct mipi_dsi_device *dsi = bl_get_data(bl);
	u8 brightness = backlight_get_brightness(bl);
	int ret;

	/* The panel takes a single 8-bit 0x51 value (downstream: 51 B8 normal, 51 FF HBM). */
	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;
	ret = mipi_dsi_dcs_write(dsi, MIPI_DCS_SET_DISPLAY_BRIGHTNESS, &brightness, 1);

	return ret < 0 ? ret : 0;
}

static const struct backlight_ops willow_bl_ops = {
	.update_status = willow_bl_update_status,
};

static struct backlight_device *willow_create_backlight(struct mipi_dsi_device *dsi)
{
	const struct backlight_properties props = {
		.type = BACKLIGHT_RAW,
		.brightness = WILLOW_BL_DEF,
		.max_brightness = WILLOW_BL_MAX,
	};

	return devm_backlight_device_register(&dsi->dev, dev_name(&dsi->dev), &dsi->dev,
					      dsi, &willow_bl_ops, &props);
}

static int willow_panel_probe(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	struct willow_panel *ctx;
	int ret;

	ctx = devm_drm_panel_alloc(dev, struct willow_panel, panel, &willow_panel_funcs,
				   DRM_MODE_CONNECTOR_DSI);
	if (IS_ERR(ctx))
		return PTR_ERR(ctx);

	/* Keep whatever level the bootloader left on the shared display/touch reset. */
	ctx->reset_gpio = devm_gpiod_get_optional(dev, "reset", GPIOD_ASIS);
	if (IS_ERR(ctx->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->reset_gpio), "failed to get reset gpio\n");

	ctx->dsi = dsi;
	mipi_dsi_set_drvdata(dsi, ctx);

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;
	dsi->mode_flags = MIPI_DSI_MODE_VIDEO | MIPI_DSI_CLOCK_NON_CONTINUOUS;

	ctx->panel.prepare_prev_first = true;

	ctx->panel.backlight = willow_create_backlight(dsi);
	if (IS_ERR(ctx->panel.backlight))
		return dev_err_probe(dev, PTR_ERR(ctx->panel.backlight),
				     "failed to create backlight\n");

	drm_panel_add(&ctx->panel);

	ret = mipi_dsi_attach(dsi);
	if (ret < 0) {
		dev_err_probe(dev, ret, "failed to attach to DSI host\n");
		drm_panel_remove(&ctx->panel);
		return ret;
	}

	return 0;
}

static void willow_panel_remove(struct mipi_dsi_device *dsi)
{
	struct willow_panel *ctx = mipi_dsi_get_drvdata(dsi);
	int ret;

	ret = mipi_dsi_detach(dsi);
	if (ret < 0)
		dev_err(&dsi->dev, "failed to detach from DSI host: %d\n", ret);

	drm_panel_remove(&ctx->panel);
}

static const struct of_device_id willow_panel_of_match[] = {
	{ .compatible = "xiaomi,willow-tianma-nt36672a" },
	{ }
};
MODULE_DEVICE_TABLE(of, willow_panel_of_match);

static struct mipi_dsi_driver willow_panel_driver = {
	.probe = willow_panel_probe,
	.remove = willow_panel_remove,
	.driver = {
		.name = "panel-xiaomi-willow-tianma",
		.of_match_table = willow_panel_of_match,
	},
};
module_mipi_dsi_driver(willow_panel_driver);

MODULE_DESCRIPTION("Tianma NT36672A panel driver for Xiaomi Redmi Note 8T (willow)");
MODULE_LICENSE("GPL");
